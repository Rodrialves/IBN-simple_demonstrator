from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication, route, Response
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import json

# REST API name
rest_api_instance_name = 'link_manager_api'

class LinkManagerRyu(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(LinkManagerRyu, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(LinkManagerController, {rest_api_instance_name: self})
        self.datapaths = {}
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.datapaths[dpid] = datapath

        # Install table-miss flow entry
        self.logger.info("Installing table-miss flow on switch %s", dpid)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    def delete_flow(self, datapath, match):
        """Delete a specific flow entry."""
        parser = datapath.ofproto_parser
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=datapath.ofproto.OFPFC_DELETE,
            out_port=datapath.ofproto.OFPP_ANY,
            out_group=datapath.ofproto.OFPG_ANY,
            match=match
        )
        datapath.send_msg(flow_mod)



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn the source MAC address
        self.mac_to_port[dpid][src] = in_port
        #self.logger.info("Packet in switch %s: src=%s, dst=%s, in_port=%s", dpid, src, dst, in_port)

        # Determine the output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow for known destinations
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)

        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def block_link(self):
        """Block the link between s1 and s2."""
        if 1 in self.datapaths and 2 in self.datapaths:
            s1 = self.datapaths[1]
            s2 = self.datapaths[2]
            parser1 = s1.ofproto_parser
            parser2 = s2.ofproto_parser

            # Delete all flows related to traffic between s1 and s2
            match_s1 = parser1.OFPMatch(in_port=4)  # Assuming s1's port 2 connects to s2
            match_s2 = parser2.OFPMatch(in_port=2)  # Assuming s2's port 1 connects to s1
            self.delete_flow(s1, match_s1)
            self.delete_flow(s2, match_s2)

            # Install drop rules to block s1 -> s2 and s2 -> s1
            drop_match_s1_to_s2 = parser1.OFPMatch(eth_type=0x0800, in_port=4)
            drop_match_s2_to_s1 = parser2.OFPMatch(eth_type=0x0800, in_port=2)
            self.add_flow(s1, 2, drop_match_s1_to_s2, [])  # Priority 2 drop
            self.add_flow(s2, 2, drop_match_s2_to_s1, [])  # Priority 2 drop

            self.logger.info("Blocked link between s1 and s2.")



    def unblock_link(self):
        """Unblock the link between s1 and s2."""
        if 1 in self.datapaths and 2 in self.datapaths:
            s1 = self.datapaths[1]
            s2 = self.datapaths[2]
            parser1 = s1.ofproto_parser
            parser2 = s2.ofproto_parser

            # Remove drop rules to restore connectivity
            drop_match_s1_to_s2 = parser1.OFPMatch(eth_type=0x0800, in_port=4)
            drop_match_s2_to_s1 = parser2.OFPMatch(eth_type=0x0800, in_port=2)
            self.delete_flow(s1, drop_match_s1_to_s2)
            self.delete_flow(s2, drop_match_s2_to_s1)

            # Add forwarding rules for s1 -> s2 and s2 -> s1
            forward_match_s1_to_s2 = parser1.OFPMatch(eth_type=0x0800)
            forward_match_s2_to_s1 = parser2.OFPMatch(eth_type=0x0800)
            actions_s1 = [parser1.OFPActionOutput(4)]
            actions_s2 = [parser2.OFPActionOutput(2)]
            self.add_flow(s1, 1, forward_match_s1_to_s2, actions_s1)  # Priority 1 forward
            self.add_flow(s2, 1, forward_match_s2_to_s1, actions_s2)  # Priority 1 forward

            self.logger.info("Unblocked link between s1 and s2.")




class LinkManagerController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(LinkManagerController, self).__init__(req, link, data, **config)
        self.controller = data[rest_api_instance_name]
        self.controller.logger.info("LinkManagerController initialized successfully.")

    # POST method to block the link
    @route('link_manager_down', '/link/down', methods=['POST'])
    def block_link_endpoint(self, req, **kwargs):
        self.controller.logger.info("Received API call to block link")
        self.controller.block_link()
        return Response(content_type='application/json', body=json.dumps({'status': 'Link blocked'}))

    # POST method to unblock the link
    @route('link_manager_up', '/link/up', methods=['POST'])
    def unblock_link_endpoint(self, req, **kwargs):
        self.controller.logger.info("Received API call to unblock link")
        self.controller.unblock_link()
        return Response(content_type='application/json', body=json.dumps({'status': 'Link unblocked'}))
