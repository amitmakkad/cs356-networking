from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4
from ryu.lib.packet import ether_types
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_all_host
from ryu.lib import hub

import time
import random
import socket
import json

import routing.routing as routing

SERVICE_TYPE = "MAC"

def swap(s1, s2):
    if s1>s2:
        return s2,s1
    return s1,s2

def file_write_line(f, line):
    for data in line:
        f.write(str(data))
        f.write(" ")
    f.write("\n")

def input_data(self):

    f = open("input/topology.txt", "r")
    
    self.num_hosts, self.num_switches = list(map(int,f.readline().split(' ')))

    for i in range(self.num_hosts):
        list(map(int,f.readline().split(' ')))

    link = f.readline()

    print("here")

    while link:
        
        s1, s2, bw, delay = list(map(int,link.split(' ')))
        s1,s2 = swap(s1,s2)
        self.bandwidth[(s1,s2)], self.delay[(s1,s2)] = bw, delay

        link = f.readline()
        
    f.close()


class SimpleSwitch13(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

        self.topology_api_app = self
        self.mac_to_port = {}

        self.num_hosts = 0
        self.num_switches = 0

        self.switches = []
        self.hosts = []
        self.edges = []

        self.bandwidth = {}
        self.delay = {}

        self.host_port = {
            1: (1,1),
            2: (5,1),
            3: (6,1),
            4: (7,1)
        }

        self.datapaths = {}

        self.flows_added = False
        self.optimal_paths = {}

        self.monitor_thread = hub.spawn(self._monitor)

        self.host_mac = {
        } 

        self.host_ipv4 = {
        } 

        input_data(self)


    def add_flow(self, datapath, priority, match, actions, buffer_id=None):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        
        cookie = random.randint(0, 0xffffffffffffffff)

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, cookie=cookie, cookie_mask=0xffffffffffffffff)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, cookie=cookie, cookie_mask=0xffffffffffffffff)
        datapath.send_msg(mod)

    def clear_flows(self):

        for dpid in self.switches:

            datapath = self.datapaths[dpid]
                        
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_type=0x0800)
            mod = parser.OFPFlowMod(
                datapath=datapath,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=match
            )
            datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        flows = []
        print("\n Switch = ",ev.msg.datapath.id)
        for stat in ev.msg.body:
            flows.append({
                "match": stat.match,
                "actions": stat.instructions[0].actions
            })
        print("Flows: {}".format(flows))
        print("\n")

    def show_flows(self):
        for dpid in self.switches:
            datapath = self.datapaths[dpid]
            parser = datapath.ofproto_parser
            req = parser.OFPFlowStatsRequest(datapath)
            datapath.send_msg(req)

    def add_optimal_flows(self):

        try:

            self.flows_added = False
            self.clear_flows()
        
            for (h1, h2), path in self.optimal_paths.items():

                if SERVICE_TYPE == "IPV4":
                    src = self.interface_to_ipv4["h" + str(h1)]
                    dst = self.interface_to_ipv4["h" + str(h2)]
                else:
                    src = self.interface_to_mac["h" + str(h1)]
                    dst = self.interface_to_mac["h" + str(h2)]

                for i in range(len(path)):

                    (dpid, in_port, out_port) = path[i]

                    datapath = self.datapaths[dpid]
                    
                    parser = datapath.ofproto_parser

                    if SERVICE_TYPE == "IPV4":
                        match = parser.OFPMatch(in_port=in_port,eth_type=0x0800,ipv4_dst=dst) 
                    else:
                        match = parser.OFPMatch(in_port=in_port,eth_type=0x0800,eth_dst=dst) 
                    
                    actions = [parser.OFPActionOutput(out_port)]

                    self.add_flow(datapath, 1, match, actions)

            self.show_flows()
            self.flows_added = True

        except Exception as E:
            print(E)
            self.flows_added = False
    
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        switch_list = get_switch(self.topology_api_app, None)
        self.switches = [switch.dp.id for switch in switch_list]
        edge_list = get_link(self.topology_api_app, None)
        self.edges = [[(link.src.dpid, link.src.port_no), (link.dst.dpid, link.dst.port_no)] for link in edge_list if link.src.dpid < link.dst.dpid]
        host_list = get_all_host(self.topology_api_app)
        self.hosts = [host.mac for host in host_list]
        for host in host_list:
            print("ip = ",host.ipv4)

        print ("switches ", self.switches)
        print ("links ", self.edges)
        print("hosts ",self.hosts)

        if len(self.switches) == self.num_switches and not self.flows_added:
            self.flow_watcher()
            time.sleep(2)


    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):
        host = ev.host
        self.logger.info("Host %s joined network on port %d of switch %s", host.mac, host.port.port_no, host.port.dpid)

    def get_link_params(self, s1, s2):
        s1,s2 = swap(s1,s2)
        return self.bandwidth[(s1,s2)], self.delay[(s1,s2)]
    
    def update_route_bandwidth(self, optimal_paths, query):

        if query is None:
            return
        
        try:
            h1, h2, bw = query
            path = optimal_paths[(h1,h2)]
            for i in range(len(path) - 1):
                s1, s2 = path[i][0], path[i+1][0]
                s1, s2 = swap(s1,s2)
                self.bandwidth[(s1,s2)]-=bw
                if self.bandwidth[(s1,s2)] < 0:
                    print("BW Negative Error")
        except:
            return
    
    def get_shortest_paths(self, req):

        try:

            src, dst, bw = req["src"], req["dst"], req["bw"]
            query = [src, dst, bw] if (src > 0 and dst > 0 and bw > 0) else  None

            f = open("input/graph.txt", "w+")

            if query:
                file_write_line(f, query)
            else:
                file_write_line(f, [-1])

            file_write_line(f, [self.num_hosts, self.num_switches])

            file_write_line(f, [len(self.edges)])

            for edge in self.edges:
                bw, delay = self.get_link_params(edge[0][0],edge[1][0])
                file_write_line(f, [edge[0][0], edge[0][1], edge[1][0], edge[1][1], bw, delay])

            for host, (switch, port) in self.host_port.items():
                file_write_line(f, [host, switch, port])

            f.close()

            return routing.find_optimal_paths(), query

        except Exception as E:
            print("get_shortest_paths", E)
            return -1, None


    def flow_watcher(self):

        print("Flow watcher called")

        if len(self.hosts)!=self.num_hosts or len(self.switches)!=self.num_switches:
            print("here1")
            return

        with open("input/requests.json", "r") as file:
            req = json.loads(file.read())

        if (req is None) or req["updated"] == False:
            print("here2")
            return

        optimal_paths, query = self.get_shortest_paths(req)
        
        if optimal_paths == -1:
            print("Flow watcher blocked")
            return
        
        req["updated"] = False
        with open("input/requests.json", "w+") as file:
            json.dump(req, file, indent=4)
        
        self.update_route_bandwidth(optimal_paths, query)
        self.optimal_paths = optimal_paths
        self.add_optimal_flows()
        print("Flow watcher updated paths")

    def _monitor(self):
        while True:
            self.flow_watcher()
            hub.sleep(3)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.datapaths[datapath.id] = datapath


        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        if not self.flows_added:
            return
        
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return #ignore lldp packet
            
        dst = eth.dst
        src = eth.src

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD


        actions = [parser.OFPActionOutput(out_port)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
            

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)