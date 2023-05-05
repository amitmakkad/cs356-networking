#!/usr/bin/python                                                                            
                                                                                             
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.link import TCLink

import requests
import ast
import time

import routing.routing as routing
from utils import *

class MyTopo(Topo):

    def __init__(self, *args, **params):

        self.hname_to_address = {}
        self.bandwidth = {}

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

            self.bandwidth[(s1,s2)] = bw
            self.addLink(switches[s1-1], switches[s2-1], cls=TCLink, bw = bw, delay = str(delay) + "ms")

            link = f.readline()
            
        f.close()

    def build(self):
        time.sleep(3)
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
            self.topo.hname_to_address[str(host)] = {"MAC": host.MAC(), "IPV4": host.IP()}


    def update_route_bandwidth(self, optimal_path, bw):
        
        def update_link_bandwidth(s1, s2, bw):
            if bw == 0:
                bw = 0.01
            s1, s2 = self.net.get("s"+str(s1)), self.net.get("s"+str(s2))
            for intf in s1.intfList():
                if intf.link:
                    if intf.link.intf1.node == s2 or intf.link.intf2.node == s2:
                        intf.config(bw=bw)
       
        for i in range(len(optimal_path) - 1):
            s1, s2 = optimal_path[i][0], optimal_path[i+1][0]
            s1, s2 = swap(s1,s2)
            self.topo.bandwidth[(s1,s2)]-=bw
            if self.topo.bandwidth[(s1,s2)] < 0:
                raise ValueError("BW Negative Error")
            update_link_bandwidth(s1, s2, self.topo.bandwidth[(s1,s2)])

    def path_request(self, req):
        url = "http://0.0.0.0:8080/path_request"
        headers = {"Content-Type": "application/json"}

        while True:
            response = requests.post(url, headers=headers, json=req).json()
            if response["success"]==True:
                return response["optimal_path"]
            else:
                print(response["message"])
            time.sleep(1)


    def service_request(self, req):
        url = "http://0.0.0.0:8080/service_request"
        headers = {"Content-Type": "application/json"}

        while True:
            response = requests.post(url, headers=headers, json=req).json()
            if response["success"]==True:
                return response["optimal_path"]
            else:
                print(response["message"])
            time.sleep(1)

    def get_host_from_address(self, addr, service_type):
        for key, value in self.topo.hname_to_address.items():
            if value[service_type] == addr:
                return self.net.get(key)

    def begin(self):
        self.net.start()
        self.show_network_info()
        self.service_request({
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

    def do_paths(self, line):

        try:

            cmd = line.strip().split(' ')

            hname_src = cmd[0]

            if (hname_src not in self.network.topo.hname_to_address):
                raise self.CommandException("Choose Valid Host Name")
            
            for host in self.network.net.hosts:

                hname_dst = host.name

                if hname_dst != hname_src:

                    optimal_path = ast.literal_eval(self.network.path_request({
                        "src": self.network.topo.hname_to_address[hname_src]["MAC"],
                        "dst": self.network.topo.hname_to_address[hname_dst]["MAC"],
                        "service_type": "MAC",
                        "bw": -1
                    }))

                    print(hname_src,"-",hname_dst,":",end=' ')

                    print(hname_src, end=' ')
                    for node in optimal_path:
                        print('s',node[0],sep='',end=' ')
                    print(hname_dst)

        except Exception as E:
            print("Could not execute path request...", E)
        
        
    def do_service(self, line):

        try:
            cmd = line.strip().split(' ')

            service_type = cmd[2]

            if service_type!='IPV4' and service_type!='MAC':
                raise self.CommandException("Choose a Valid Service Type")
            
            src, dst = cmd[0], cmd[1]
            bw = int(cmd[3])

            optimal_path = ast.literal_eval(self.network.service_request({
                "src": src,
                "dst": dst,
                "service_type": service_type,
                "bw": bw,
            }))

            print("Connection generated using the path:")
            for node in optimal_path:
                print('s',node[0],sep='',end=' ')
            print()

            h1, h2 = self.network.get_host_from_address(src, service_type), self.network.get_host_from_address(dst, service_type)
            h1.cmd('xterm -e iperf -s &')
            time.sleep(2)
            h2.cmd('xterm -hold -e iperf -c %s -t 5 -b %dM' % (h1.IP(), bw))

            self.network.update_route_bandwidth(optimal_path, bw)
            print()

        except Exception as E:
            print("Could not execute connection request...", E)

if __name__ == '__main__':
    setLogLevel('info')
    Network().begin()
    


