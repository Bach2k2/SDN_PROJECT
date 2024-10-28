from mininet.topo import Topo
from mininet.net import Mininet
# from mininet.node import CPULimitedHost
from mininet.link import TCLink
# from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
# from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController
from time import sleep

from datetime import datetime
from random import randrange, choice

class MyTopo( Topo ):

    def build( self ):

         # Routers
        r1 = self.addHost('r1', ip='192.168.1.1/24')
        r2 = self.addHost('r2', ip='192.168.2.1/24')
        r3 = self.addHost('r3', ip='192.168.3.1/24')
        r4 = self.addHost('r4', ip='192.168.4.1/24')

        # Switches
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Hosts
        h1 = self.addHost('h1', cpu=1.0/20, mac="00:00:00:00:00:01", ip='192.168.1.10/24')
        h2 = self.addHost('h2', cpu=1.0/20, mac="00:00:00:00:00:02", ip='192.168.1.11/24')
        h3 = self.addHost('h3', cpu=1.0/20, mac="00:00:00:00:00:03", ip='192.168.2.10/24')
        h4 = self.addHost('h4', cpu=1.0/20, mac="00:00:00:00:00:04", ip='192.168.2.11/24')
        h5 = self.addHost('h5', cpu=1.0/20, mac="00:00:00:00:00:05", ip='192.168.3.10/24')
        h6 = self.addHost('h6', cpu=1.0/20, mac="00:00:00:00:00:06", ip='192.168.3.11/24')
        h7 = self.addHost('h7', cpu=1.0/20, mac="00:00:00:00:00:07", ip='192.168.4.10/24')
        h8 = self.addHost('h8', cpu=1.0/20, mac="00:00:00:00:00:08", ip='192.168.4.11/24')

        # Add links between routers and switches
        self.addLink(r1, s1)
        self.addLink(r2, s2)
        self.addLink(r3, s3)
        self.addLink(r4, s4)

        # Add links between hosts and switches
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(h5, s3)
        self.addLink(h6, s3)
        self.addLink(h7, s4)
        self.addLink(h8, s4)

        # Add inter-switch links
        self.addLink(r1, r2, params1={'ip': '192.168.10.1/24'}, params2={'ip': '192.168.10.2/24'})
        self.addLink(r2, r3, params1={'ip': '192.168.20.1/24'}, params2={'ip': '192.168.20.2/24'})
        self.addLink(r3, r4, params1={'ip': '192.168.30.1/24'}, params2={'ip': '192.168.30.2/24'})
def ip_generator():
    return ".".join(["192", "168", str(randrange(1, 4)), str(randrange(10, 11))])

def startNetwork():

    #print "Starting Network"
    topo = MyTopo()

    c0 = RemoteController('c0', ip='192.168.245.128', port=6653)
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()
    
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')
    h5 = net.get('h5')
    h6 = net.get('h6')
    h7 = net.get('h7')
    h8 = net.get('h8')
    
    r1 = net.get('r1')
    r2 = net.get('r2')
    r3 = net.get('r3')
    r4 = net.get('r4')
    print(r1.cmd('ifconfig'))
    
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')
    r4.cmd('sysctl -w net.ipv4.ip_forward=1')
    
    r1.cmd('ip route add 10.0.2.0/24 via 192.168.10.2')

    r2.cmd('ip route add 10.0.1.0/24 via 192.168.10.1')
    r2.cmd('ip route add 10.0.3.0/24 via 192.168.20.2')

    r3.cmd('ip route add 10.0.2.0/24 via 192.168.20.1')
    r3.cmd('ip route add 10.0.4.0/24 via 192.168.30.2')

    r4.cmd('ip route add 10.0.3.0/24 via 192.168.30.1')

    r1.cmd('ip route add 10.0.3.0/24 via 192.168.10.2')
    r1.cmd('ip route add 10.0.4.0/24 via 192.168.10.2')

    r2.cmd('ip route add 10.0.4.0/24 via 192.168.20.2')
    r3.cmd('ip route add 10.0.1.0/24 via 192.168.20.1')

    r4.cmd('ip route add 10.0.1.0/24 via 192.168.30.1')
    r4.cmd('ip route add 10.0.2.0/24 via 192.168.30.1')

    
    hosts = [h1, h2, h3, h4, h5, h6, h7, h8]
    
    h1.cmd('cd /home/mininet/webserver')
    h1.cmd('python -m SimpleHTTPServer 80 &')
    
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing ICMP (Ping) Flood")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -1 -V -d 120 -w 64 -p 80 --rand-source --flood {}".format(dst))  
    sleep(100)
        
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing UDP Flood")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -2 -V -d 120 -w 64 --rand-source --flood {}".format(dst))    
    sleep(100)
    
    src = choice(hosts)
    dst = ip_generator()    
    print("--------------------------------------------------------------------------------")
    print("Performing TCP-SYN Flood")  
    print("--------------------------------------------------------------------------------")
    src.cmd('timeout 20s hping3 -S -V -d 120 -w 64 -p 80 --rand-source --flood 10.0.0.1')
    sleep(100)
    
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing LAND Attack")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -1 -V -d 120 -w 64 --flood -a {} {}".format(dst,dst))
    sleep(100)  
    print("--------------------------------------------------------------------------------")

    # CLI(net)
    net.stop()

if __name__ == '__main__':
    
    start = datetime.now()
    
    setLogLevel( 'info' )
    startNetwork()
    
    end = datetime.now()
    
    print(end-start)