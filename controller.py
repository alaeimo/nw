from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp

class NetworkSlicingController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(NetworkSlicingController, self).__init__(*args, **kwargs)

        # out_port = self.switch_4_ports_mapper[in_port]
        self.switch_4_ports_mapper = {1:3, 3:1, 2:4, 4:2}

        # outport = self.mac_to_port[dpid][destination_mac_address]
        self.mac_to_port = {
            1: {"00:00:00:00:00:01": 3, "00:00:00:00:00:02": 4},
            6: {"00:00:00:00:00:05": 3, "00:00:00:00:00:06": 4},
            2: {"00:00:00:00:00:03": 3, "00:00:00:00:00:04": 4,
                "00:00:00:00:00:07": 1, "00:00:00:00:00:08": 2},
            5: {"00:00:00:00:00:03": 1, "00:00:00:00:00:04": 1,
                "00:00:00:00:00:07": 2, "00:00:00:00:00:08": 2},
            7: {"00:00:00:00:00:03": 1, "00:00:00:00:00:04": 2,
                "00:00:00:00:00:07": 3, "00:00:00:00:00:08": 4},
        }

        # out_port = self.slice_ports[dpid][slice_number]
        self.TCP_SERVICE_SLICE_NUMBER = 1
        self.UDP_SERVICE_SLICE_NUMBER = 2

        self.slice_ports = {1: {self.TCP_SERVICE_SLICE_NUMBER: 1, self.UDP_SERVICE_SLICE_NUMBER: 2}, 
                            6: {self.TCP_SERVICE_SLICE_NUMBER: 1, self.UDP_SERVICE_SLICE_NUMBER: 2}}
        
        self.end_swtiches = [1, 6]
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        # Apply topology slicing rules on switch 4
        if dpid == 4:
            out_port = self.switch_4_ports_mapper[in_port]
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)
        
        elif dpid in self.mac_to_port:
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                match = datapath.ofproto_parser.OFPMatch(eth_dst=dst)
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)
            
            # Apply service slicing rules
            elif pkt.get_protocol(tcp.tcp):
                slice_number =  self.TCP_SERVICE_SLICE_NUMBER
                if dpid in self.slice_ports and slice_number in self.slice_ports[dpid]:
                    out_port = self.slice_ports[dpid][slice_number]
                    match = datapath.ofproto_parser.OFPMatch(
                        in_port=in_port,
                        eth_dst=dst,
                        eth_src=src,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ip_proto=0x06,  # TCP
                    )
                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                    self.add_flow(datapath, 1, match, actions)
                    self._send_package(msg, datapath, in_port, actions)
            
            elif pkt.get_protocol(udp.udp):
                slice_number =  self.UDP_SERVICE_SLICE_NUMBER
                if dpid in self.slice_ports and slice_number in self.slice_ports[dpid]:
                    out_port = self.slice_ports[dpid][slice_number]
                    match = datapath.ofproto_parser.OFPMatch(
                        in_port=in_port,
                        eth_dst=dst,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ip_proto=0x11,  # UDP
                        udp_dst=pkt.get_protocol(udp.udp).dst_port,
                    )
                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                    self.add_flow(datapath, 2, match, actions)
                    self._send_package(msg, datapath, in_port, actions)
    
            elif pkt.get_protocol(icmp.icmp):
                slice_number = self.TCP_SERVICE_SLICE_NUMBER
                if dpid in self.slice_ports and slice_number in self.slice_ports[dpid]:
                    out_port = self.slice_ports[dpid][slice_number]
                    match = datapath.ofproto_parser.OFPMatch(
                        in_port=in_port,
                        eth_dst=dst,
                        eth_src=src,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ip_proto=0x01,  # ICMP
                    )
                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                    self.add_flow(datapath, 1, match, actions)
                    self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)