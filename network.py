#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_network():
    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    info("*** Adding controller\n")
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    info("*** Adding Hosts _ Pink Slice ***\n")
    H1 = net.addHost('H1', ip='10.0.0.1')
    H2 = net.addHost('H2', ip='10.0.0.2')
    H5 = net.addHost('H5', ip='10.0.0.5')
    H6 = net.addHost('H6', ip='10.0.0.6')

    info("*** Adding Switches _ Pink Slice ***\n")
    S1 = net.addSwitch('S1')
    S3 = net.addSwitch('S3')
    S6 = net.addSwitch('S6')
    S4 = net.addSwitch('S4')

    info("*** Creating Links With Specified Ports _ Pink Slice ***\n")
    net.addLink(H1 , S1 , port1=1 , port2=3)
    net.addLink(H2 , S1 , port1=1 , port2=4)
    net.addLink(S1 , S3 , port1=1 , port2=1)
    net.addLink(S1 , S4 , port1=2 , port2=1)
    net.addLink(S3 , S6 , port1=2 , port2=1)
    net.addLink(S4 , S6 , port1=3 , port2=2)
    net.addLink(S6 , H5 , port1=3 , port2=1)
    net.addLink(S6 , H6 , port1=4 , port2=1)

    info("*** Adding Hosts _ Blue Slice ***\n")
    H3 = net.addHost('H3', ip='10.0.0.3')
    H4 = net.addHost('H4', ip='10.0.0.4')
    H7 = net.addHost('H7', ip='10.0.0.7')
    H8 = net.addHost('H8', ip='10.0.0.8')

    info("*** Adding Switches _ Blue Slice ***\n")
    S2 = net.addSwitch('S2')
    S5 = net.addSwitch('S5')
    S7 = net.addSwitch('S7')

    info("*** Creating Links With Specified Ports _ Blue Slice ***\n")

    net.addLink(H3 , S2 , port1=1 , port2=3)
    net.addLink(H4 , S2 , port1=1 , port2=4)
    net.addLink(S2 , S4 , port1=1 , port2=2)
    net.addLink(S2 , S5 , port1=2 , port2=1)
    net.addLink(S4 , S7 , port1=4 , port2=1)
    net.addLink(S5 , S7 , port1=2 , port2=2)
    net.addLink(S7 , H7 , port1=3 , port2=1)
    net.addLink(S7 , H8 , port1=4 , port2=1)

    info("*** Starting Network\n")
    net.start()

    info("*** Adding flow rules to Swith 4 to block traffic between pink slice and blue slice ***\n")

    info("*** LEFT_UP TO LEFT_DOWN ***\n")
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.1,nw_dst=10.0.0.3,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.1,nw_dst=10.0.0.4,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.2,nw_dst=10.0.0.3,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.2,nw_dst=10.0.0.4,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.3,nw_dst=10.0.0.1,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.3,nw_dst=10.0.0.2,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.4,nw_dst=10.0.0.1,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.4,nw_dst=10.0.0.2,actions=drop')

    info("*** RIGHT_UP TO RIGHT_DOWN ***\n")
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.5,nw_dst=10.0.0.7,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.5,nw_dst=10.0.0.8,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.6,nw_dst=10.0.0.7,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.6,nw_dst=10.0.0.8,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.7,nw_dst=10.0.0.5,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.7,nw_dst=10.0.0.6,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.8,nw_dst=10.0.0.5,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.8,nw_dst=10.0.0.6,actions=drop')

    info("*** LEFT_UP TO RIGHT_DOWN ***\n")
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.1,nw_dst=10.0.0.7,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.1,nw_dst=10.0.0.8,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.2,nw_dst=10.0.0.7,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.2,nw_dst=10.0.0.8,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.7,nw_dst=10.0.0.1,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.7,nw_dst=10.0.0.2,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.8,nw_dst=10.0.0.1,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.8,nw_dst=10.0.0.2,actions=drop')

    info("*** RIGHT_UP TO LEFT_DOWN ***\n")
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.5,nw_dst=10.0.0.3,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.5,nw_dst=10.0.0.4,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.6,nw_dst=10.0.0.3,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.6,nw_dst=10.0.0.4,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.3,nw_dst=10.0.0.5,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.3,nw_dst=10.0.0.6,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.4,nw_dst=10.0.0.5,actions=drop')
    S4.cmd('ovs-ofctl add-flow S4 priority=10,ip,nw_src=10.0.0.4,nw_dst=10.0.0.6,actions=drop')

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_network()

