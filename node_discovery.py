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

import routing.routing as routing

NUM_SWITCHES = 3
SERVICE_TYPE = "IPV4"

class SimpleSwitch13(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

        self.topology_api_app = self
        self.mac_to_port = {}

        self.switches = []
        self.links = []
        self.hosts = []

        self.datapaths = {}

        self.flows_added = False
        self.optimal_paths = {}

        self.monitor_thread = hub.spawn(self._monitor)

        self.interface_to_ipv4 = {
            "h1": "10.0.0.1",
            "h2": "10.0.0.2",
            "h3": "10.0.0.3"
        } 

        self.interface_to_mac = {
            "h1": "00:00:00:00:00:01",
            "h2": "00:00:00:00:00:02",
            "h3": "00:00:00:00:00:03"
        } 


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
    

    def flow_watcher(self):
        print("Flow watcher called")
        paths = routing.get_shortest_paths()
        if paths == -1:
            print("Flow watcher blocked")
            return
        self.optimal_paths = paths
        self.add_optimal_flows()
        print("Flow watcher updated paths")

    def _monitor(self):
        while True:
            self.flow_watcher()
            hub.sleep(3)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        switch_list = get_switch(self.topology_api_app, None)
        self.switches = [switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        self.links = [(link.src.dpid, link.dst.dpid, {"s_port": link.src.port_no, "d_port": link.dst.port_no}) for link in links_list]
    
        print ("switches ", self.switches)
        print ("links ", self.links)

        if len(self.switches) == NUM_SWITCHES and not self.flows_added:
            self.flow_watcher()
            time.sleep(2)


    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):
        host = ev.host
        self.logger.info("Host %s joined network on port %d of switch %s", host.mac, host.port.port_no, host.port.dpid)


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