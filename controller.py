from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp

class NetworkSlicingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkSlicingController, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Define traffic forbidden rules
        if datapath.id == 4:
            self.add_block_rules(parser, datapath)

        # Define slicing rules for pink slice
        if datapath.id in [1, 3, 6]:
            self.add_pink_slice_rules(parser, datapath)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    def add_block_rules(self, parser, datapath):
        ofproto = datapath.ofproto

        # Block traffic from port 1 to ports 2 and 4 and vice versa
        # block_pairs = [(1, 2), (1, 4), (3, 2), (3, 4)]

        # for in_port, out_port in block_pairs:
        #     match = parser.OFPMatch(in_port=in_port, eth_type=0x0800)
        #     actions = []
        #     self.add_flow(datapath, 10, match, actions)
            
        #     match = parser.OFPMatch(in_port=out_port, eth_type=0x0800)
        #     actions = []
        #     self.add_flow(datapath, 10, match, actions)

        # Ensure traffic between port 1 and port 3 is allowed
        # allow_pairs = [(1, 3), (3, 1), (2, 4), (4, 2)]

        # for in_port, out_port in allow_pairs:
        #     match = parser.OFPMatch(in_port=in_port, eth_type=0x0800)
        #     actions = [parser.OFPActionOutput(out_port)]
        #     self.add_flow(datapath, 10, match, actions)


    def add_pink_slice_rules(self, parser, datapath):
        ofproto = datapath.ofproto

        # TCP traffic through S1-S3-S6 path
        if datapath.id == 1:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=6)  # TCP
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 10, match, actions)
        
        if datapath.id == 3:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=6)  # TCP
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 10, match, actions)

        if datapath.id == 6:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=6)  # TCP
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 10, match, actions)

        # UDP traffic through S1-S4-S6 path
        if datapath.id == 1:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17)  # UDP
            actions = [parser.OFPActionOutput(4)]
            self.add_flow(datapath, 10, match, actions)
        
        if datapath.id == 4:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17)  # UDP
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 10, match, actions)

        if datapath.id == 6:
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17)  # UDP
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 10, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == 0x0800:
            ip = pkt.get_protocols(ipv4.ipv4)[0]

            if ip.proto == 6:  # TCP
                match = parser.OFPMatch(eth_type=0x0800, ip_proto=6)
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                self.add_flow(datapath, 1, match, actions)

            elif ip.proto == 17:  # UDP
                match = parser.OFPMatch(eth_type=0x0800, ip_proto=17)
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                self.add_flow(datapath, 1, match, actions)

        elif eth.ethertype == 0x0800 and ip.proto == 1:  # ICMP
            # if datapath.id == 4:
            #     # Drop ICMP traffic between pink and blue slices
            #     actions = []
            #     match = parser.OFPMatch(eth_type=0x0800, ip_proto=1)
            #     self.add_flow(datapath, 10, match, actions)
            # else:
                # Flood ICMP traffic within slices
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            match = parser.OFPMatch(eth_type=0x0800, ip_proto=1)
            self.add_flow(datapath, 1, match, actions)

        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
