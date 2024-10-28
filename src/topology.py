#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():
    
    net = Mininet( topo=None,
                   build=False, controller=RemoteController,
                   ipBase='10.0.0.0/8')
    net.addController('c1',controller=RemoteController,ip='127.0.0.1',port=6653)

    info( '*** Adding controller\n' )

    info('*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, failMode='standalone')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, failMode='standalone')

    info('*** Add routers\n')
    r1 = net.addHost('r1', cls=Node, ip='192.168.1.1/24')
    r2 = net.addHost('r2', cls=Node, ip='192.168.2.1/24')
    r3 = net.addHost('r3', cls=Node, ip='192.168.3.1/24')
    r4 = net.addHost('r4', cls=Node, ip='192.168.4.1/24')

    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')
    r4.cmd('sysctl -w net.ipv4.ip_forward=1')

    info('*** Add hosts\n')
    h1 = net.addHost('h1', cls=Node, ip='192.168.1.10/24', defaultRoute='via 192.168.1.1')
    h2 = net.addHost('h2', cls=Node, ip='192.168.1.11/24', defaultRoute='via 192.168.1.1')
    h3 = net.addHost('h3', cls=Node, ip='192.168.2.10/24', defaultRoute='via 192.168.2.1')
    h4 = net.addHost('h4', cls=Node, ip='192.168.2.11/24', defaultRoute='via 192.168.2.1')
    h5 = net.addHost('h5', cls=Node, ip='192.168.3.10/24', defaultRoute='via 192.168.3.1')
    h6 = net.addHost('h6', cls=Node, ip='192.168.3.11/24', defaultRoute='via 192.168.3.1')
    h7 = net.addHost('h7', cls=Node, ip='192.168.4.10/24', defaultRoute='via 192.168.4.1')
    h8 = net.addHost('h8', cls=Node, ip='192.168.4.11/24', defaultRoute='via 192.168.4.1')


    info('*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(s1, r1, intfName2='r1-eth0', params2={'ip': '192.168.1.1/24'})

    net.addLink(h3, s2)
    net.addLink(h4, s2)
    net.addLink(s2, r2, intfName2='r2-eth0', params2={'ip': '192.168.2.1/24'})

    net.addLink(h5, s3)
    net.addLink(h6, s3)
    net.addLink(s3, r3, intfName2='r3-eth0', params2={'ip': '192.168.3.1/24'})

    net.addLink(h7, s4)
    net.addLink(h8, s4)
    net.addLink(s4, r4, intfName2='r4-eth0', params2={'ip': '192.168.4.1/24'})

    net.addLink(r1, r2, intfName1='r1-eth1', intfName2='r2-eth1', params1={'ip': '192.168.10.1/24'}, params2={'ip': '192.168.10.2/24'})
    net.addLink(r2, r3, intfName1='r2-eth2', intfName2='r3-eth1', params1={'ip': '192.168.20.1/24'}, params2={'ip': '192.168.20.2/24'})
    net.addLink(r3, r4, intfName1='r3-eth2', intfName2='r4-eth1', params1={'ip': '192.168.30.1/24'}, params2={'ip': '192.168.30.2/24'})

    info( '*** Starting network\n')
    net.build()
    
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([])
    net.get('s2').start([])
    net.get('s3').start([])
    net.get('s4').start([])

    info( '*** Post configure switches and hosts\n')

    info( '*** Assign Routes\n')
    r1.cmd('ifconfig r1-eth1 up')
    r2.cmd('ifconfig r2-eth1 up')
    r2.cmd('ifconfig r2-eth2 up')
    r3.cmd('ifconfig r3-eth1 up')
    r3.cmd('ifconfig r3-eth2 up')
    r4.cmd('ifconfig r4-eth1 up')

    r1.cmd('ip route add 192.168.2.0/24 via 192.168.10.2')
    r1.cmd('ip route add 192.168.3.0/24 via 192.168.10.2')
    r1.cmd('ip route add 192.168.4.0/24 via 192.168.10.2')

    r2.cmd('ip route add 192.168.1.0/24 via 192.168.10.1')
    r2.cmd('ip route add 192.168.3.0/24 via 192.168.20.2')
    r2.cmd('ip route add 192.168.4.0/24 via 192.168.20.2')
    
    r3.cmd('ip route add 192.168.1.0/24 via 192.168.20.1')
    r3.cmd('ip route add 192.168.2.0/24 via 192.168.20.1')
    r3.cmd('ip route add 192.168.4.0/24 via 192.168.30.2')

    r4.cmd('ip route add 192.168.3.0/24 via 192.168.30.1')
    r4.cmd('ip route add 192.168.1.0/24 via 192.168.30.1')
    r4.cmd('ip route add 192.168.2.0/24 via 192.168.30.1')

    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')
    r4.cmd('sysctl -w net.ipv4.ip_forward=1')


    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()