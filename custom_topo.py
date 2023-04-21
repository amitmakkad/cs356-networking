#!/usr/bin/python                                                                            
                                                                                             
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.link import TCLink

import re
import time
import urllib.request
import random
import routing.routing as routing
import json

def get_regex_num(str):
        pattern = r"\d+"
        match = re.search(pattern, str)
        if match:
            number = int(match.group())
            return number
        else:
            print("No match found")

def swap(s1, s2):
    if s1>s2:
        return s2,s1
    return s1,s2

class MyTopo(Topo):

    def __init__(self, *args, **params):
        super().__init__(*args, **params)

    def input_topology(self):

        f = open("input/topology.txt", "r")
        
        num_hosts, num_switches = list(map(int,f.readline().split(' ')))
        hosts, switches = [], []

        for i in range(1, num_hosts + 1):
            h = self.addHost("h" + str(i), ip="10.0.0."+str(i))
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

    
    def get_host_switch_port(self):

        host_port = {}

        for host in self.net.hosts:
            for intf in host.intfList():
                if intf.link:
                    node1, port_str_1 = intf.link.intf1.name.split('-')[0], intf.link.intf1.name.split('-')[1]
                    node2, port_str_2 = intf.link.intf2.name.split('-')[0], intf.link.intf2.name.split('-')[1]

                    if node1[0]=='h' and node2[0]=='s':

                        host_num, port_num_1   = get_regex_num(node1), get_regex_num(port_str_1)
                        switch_num, port_num_2 = get_regex_num(node2), get_regex_num(port_str_2)

                        host_port[host_num] = (switch_num, port_num_2)

        return host_port
    
    def get_edges(self):

        edges = []

        for switch in self.net.switches:
            for intf in switch.intfList():
                if intf.link:
                    node1, port_str_1 = intf.link.intf1.name.split('-')[0], intf.link.intf1.name.split('-')[1]
                    node2, port_str_2 = intf.link.intf2.name.split('-')[0], intf.link.intf2.name.split('-')[1]

                    if node1[0]=='s' and node2[0]=='s':

                        switch_num_1, port_num_1 = get_regex_num(node1), get_regex_num(port_str_1)
                        switch_num_2, port_num_2 = get_regex_num(node2), get_regex_num(port_str_2)

                        edge = [(switch_num_1,port_num_1),(switch_num_2,port_num_2)]
                        if switch_num_1 > switch_num_2:
                            edge[0], edge[1] = edge[1], edge[0]

                        if edge not in edges:
                            edges.append(edge)

        return edges
    
    def show_network_info(self):
        
        host_port = self.get_host_switch_port()
        edges = self.get_edges()

        print("\n")
        print("Host connections :")
        dumpNodeConnections(self.net.hosts)

        print("\n")
        print("Host MAC addresses :")
        for host in self.net.hosts:
            print(host, host.MAC())

        print("\n")
        print("Number of Hosts :",len(self.net.hosts))
        print("Number of Switches :",len(self.net.switches))

        
        print("\n")
        print("Switch to Switch Edges :")
        for edge in edges:
            # bw, delay = self.get_link_params(edge[0][0],edge[1][0])
            bw, delay = 0, 0
            print("Switch1:",edge[0][0],"Port1:",edge[0][1],"  Switch2:",edge[1][0],"Port2:",edge[1][1], "  bw =",bw, "delay =",str(delay)+'ms')
        

        print("\n")
        print("Switch to Host Edges :")
        for host, (switch, port) in host_port.items():
            print("Host:",host," Switch:",switch," Port:",port)

        print("\n")

    def request_connection(self, req):
        with open("input/requests.json", "w") as file:
                json.dump(req, file, indent=4)

    def begin(self):
        self.net.start()
        self.show_network_info()
        self.request_connection({
            "updated": True,
            "src": -1,
            "dst": -1,
            "bw": -1
        })
        CustomCLI(self)
        self.net.stop()


class CustomCLI(CLI):

    class CommandException(Exception):
        pass

    def __init__(self, network: Network,  *args, **kwargs):
        self.network = network
        super().__init__(network.net, *args, **kwargs)
    
    def get_host_num(self, addr, service_type):
        return int(addr)

    def do_service(self, line):

        try:
            cmd = line.strip().split(' ')

            service_type = cmd[2]

            if service_type!='IPV4' and service_type!='MAC':
                raise self.CommandException("Choose a Valid Service Type")
            
            src, dst = self.get_host_num(cmd[0], service_type), self.get_host_num(cmd[1], service_type)
            bw = int(cmd[3])

            self.network.request_connection({
                "updated": True,
                "src": src,
                "dst": dst,
                "bw": bw
            })
        
        except Exception as E:
            print("Invalid Command :", E)

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

