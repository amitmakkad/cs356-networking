#!/usr/bin/python                                                                            
                                                                                             
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.link import TCLink

import time
import urllib.request
import random
import json

import routing.routing as routing
from .utils import *

class MyTopo(Topo):

    def __init__(self, *args, **params):
        super().__init__(*args, **params)

    def input_topology(self):

        f = open("input/topology.txt", "r")
        
        num_hosts, num_switches = list(map(int,f.readline().split(' ')))
        hosts, switches = [], []

        for i in range(1, num_hosts + 1):
            h = self.addHost("h" + str(i))
            hosts.append(h)
        
        for i in range(1, num_switches + 1):
            s = self.addSwitch("s" + str(i))
            switches.append(s)

        
        for i in range(num_hosts):
            h_num, s_num = list(map(int,f.readline().split(' ')))
            self.addLink(hosts[h_num-1], switches[s_num-1])

        link = f.readline()

        while link:
            
            s1, s2, bw, delay = list(map(int,link.split(' ')))
            s1,s2 = swap(s1,s2)
            self.addLink(switches[s1-1], switches[s2-1], cls=TCLink, bw = bw, delay = str(delay) + "ms")

            link = f.readline()
            
        f.close()

    def build(self):
        return self.input_topology()


class Network():

    def __init__(self):
        self.topo = MyTopo()
        self.net  = Mininet(topo=self.topo, autoSetMacs=True, controller = lambda name : RemoteController(name,ip="127.0.0.1", port=6653), autoStaticArp=True)

    
    def show_network_info(self):

        print("\n")
        print("Host connections :")
        dumpNodeConnections(self.net.hosts)

        print("\n")
        print("Host MAC and IP addresses :")
        for host in self.net.hosts:
            print(host, host.MAC(), host.IP())

    def request_connection(self, req):
        with open("input/request.json", "w") as file:
                json.dump(req, file, indent=4)

    def begin(self):
        self.net.start()
        self.show_network_info()
        self.request_connection({
            "updated": True,
            "src": -1,
            "dst": -1,
            "bw": -1,
            "service_type": "MAC"
        })
        CustomCLI(self)
        self.net.stop()


class CustomCLI(CLI):

    class CommandException(Exception):
        pass

    def __init__(self, network: Network,  *args, **kwargs):
        self.network = network
        super().__init__(network.net, *args, **kwargs)

    def do_service(self, line):

        try:
            cmd = line.strip().split(' ')

            service_type = cmd[2]

            if service_type!='IPV4' and service_type!='MAC':
                raise self.CommandException("Choose a Valid Service Type")
            
            src, dst = cmd[0], cmd[1]
            bw = int(cmd[3])

            self.network.request_connection({
                "updated": True,
                "src": src,
                "dst": dst,
                "service_type": service_type,
                "bw": bw,
            })
        
        except Exception as E:
            print("Could not execute connection request...", E)

if __name__ == '__main__':
    setLogLevel('info')
    Network().begin()
    

# # Get the link between h1 and s1
# link = net.get('s2').connectionsTo(net.get('s3'))[0][0]

# # Modify the bandwidth of the link
# link.intf1.config(bw=20)

# Get input from the CLI
# input_var = input('Enter some input: ')

# # Do something with the input
# print('You entered:', input_var)



# h1, h2 = net.get('h1'), net.get('h2')

# h1.cmd('xterm -e nc -l 5000 &')
# time.sleep(2)
# h2.cmd('xterm -e echo "Hello World" | nc -q 1 -w 5 00:00:00:00:00:01 5000')

# h1.cmd('xterm -e python3 -m http.server 80 &')
# time.sleep(2)

# output = h2.cmd('time wget -O - http://%s:80' % h1.IP())
# print(output.split(' '))

