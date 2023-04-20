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
import routing

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

        self.bandwidth = {}
        self.delay = {}

        super().__init__(*args, **params)

    def input_topology(self):

        f = open("input/topology.txt")
        
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

            self.bandwidth[(s1,s2)], self.delay[(s1,s2)] = bw, delay
            self.addLink(switches[s1-1], switches[s2-1], cls=TCLink, bw = bw, delay = str(delay) + "ms")

            link = f.readline()
            
        f.close()

    def build(self):
        return self.input_topology()


class Network():

    def __init__(self):
        self.topo = MyTopo()
        self.net  = Mininet(topo=self.topo, autoSetMacs=True, controller = lambda name : RemoteController(name,ip="127.0.0.1", port=6653), autoStaticArp=True)

    def get_link_params(self, s1, s2):
        s1,s2 = swap(s1,s2)
        return self.topo.bandwidth[(s1,s2)], self.topo.delay[(s1,s2)]
    
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
            bw, delay = self.get_link_params(edge[0][0],edge[1][0])
            print("Switch1:",edge[0][0],"Port1:",edge[0][1],"  Switch2:",edge[1][0],"Port2:",edge[1][1], "  bw =",bw, "delay =",str(delay)+'ms')
        

        print("\n")
        print("Switch to Host Edges :")
        for host, (switch, port) in host_port.items():
            print("Host =",host," Switch = ",switch," Port =",port)

        print("\n")

    def update_route_bandwidth(self, optimal_paths, query):

        if query is None:
            return
        
        def update_link_bandwidth(s1, s2, bw):
            s1, s2 = self.net.get("s"+str(s1)), self.net.get("s"+str(s2))
            for intf in s1.intfList():
                if intf.link:
                    if intf.link.intf1.node == s2 or intf.link.intf2.node == s2:
                        res = intf.config(bw=bw)
        try:
            h1, h2, bw = query
            path = optimal_paths[(h1,h2)]
            for i in range(len(path) - 1):
                s1, s2 = path[i][0], path[i+1][0]
                s1, s2 = swap(s1,s2)
                self.topo.bandwidth[(s1,s2)]-=bw
                update_link_bandwidth(s1, s2, self.topo.bandwidth[(s1,s2)])
                if self.topo.bandwidth[(s1,s2)] < 0:
                    print("BW Negative Error")
        except:
            return


    def update_routes(self, query):
        
        host_port = self.get_host_switch_port()
        edges = self.get_edges()

        f = open("input/graph.txt","w+")

        def file_write_line(f, line):
            for data in line:
                f.write(str(data))
                f.write(" ")
            f.write("\n")

        if query is not None:
            file_write_line(f, query)
        else:
            file_write_line(f, [-1])

        file_write_line(f, [len(self.net.hosts), len(self.net.switches)])

        file_write_line(f, [len(edges)])

        for edge in edges:
            bw, delay = self.get_link_params(edge[0][0],edge[1][0])
            file_write_line(f, [edge[0][0], edge[0][1], edge[1][0], edge[1][1], bw, delay])

        for host, (switch, port) in host_port.items():
            file_write_line(f, [host, switch, port])

        f.close()

        optimal_paths = routing.find_shortest_paths()
        self.update_route_bandwidth(optimal_paths, query)

    def begin(self):
        self.net.start()
        self.show_network_info()
        self.update_routes(None)
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
            
            bw = float(cmd[3])
            self.network.update_routes([src, dst, bw])

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

