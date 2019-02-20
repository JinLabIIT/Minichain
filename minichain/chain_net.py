from time import sleep, asctime

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import TCLink
from go_ether import GoEthereum

class MiniChain(Mininet):
    """
    TODO:
        2. adjust UI
        3. peers management
            3.2 peers monitor
        4. network contained bootnode
    """
    def __init__(self, chain_topo=None, tdf = 1, **params):
        Mininet.__init__(self,link=TCLink,**params)
        self.name_to_peer={}
        self.s1_node_to_port={}
        self.s1_max_port = 0
        self.chain_topo = chain_topo
        self.tdf = tdf

        self.s1 = self.addSwitch('s1', protocols='OpenFlow13', failMode='standalone')

        if chain_topo is not None:
            self.buildChainTopo()

    def add_peer(self, name,cls=None,**params):
        """
        Add peer after starting network
        """
        if not cls is None:
            peer = self.addHost(name, cls, subnet=self.ipBase, **params)
        else:
            raise Exception("peer class does not specified\n")

        self.addLink(self.s1, peer, port1=self.s1_max_port+1)
        self.s1_max_port+=1
        self.s1_node_to_port[name] = self.s1_max_port
        self.name_to_peer[name] = peer
        return peer

    def del_peer(self, peer):
        peer.stop_node()
        self.name_to_peer.pop(peer.name)
        self.delNode(peer)

    def linksBetween( self, node1, node2 ):
        "Return Links between node1 and node2"
        return [ link for link in self.links
                 if ( node1, node2 ) in (
                    ( link.intf1.node, link.intf2.node ),
                    ( link.intf2.node, link.intf1.node ) ) ]

    def add_edge(self, peer1, peer2, bw=None, delay=None, jitter=None, loss=None, max_queue_size=None, flag=True):
        """
        Add edge after starting peer
        Edge parameters:
            1. *bandwidth
            2. delay
            3. jitter
            4. loss
            5. max queue size
        """
        def bw_cmds(intf_name,classid, ip_src, bw=None):
            if bw is None: bw=10
            cmds = []
            cmds+=["tc class add dev %s parent 1:0 classid 1:%d htb rate %dmbit burst 1" % (intf_name,classid,bw)]
            cmd = "tc filter add dev %s parent 1:0 protocol ip u32 match ip src %s flowid %s" % (intf_name, ip_src, "1:%d"%classid)
            cmds.append(cmd)
            return cmds, "1:%d"%classid

        def lat_cmds(parent, intf_name, delay=None, jitter=None, loss=None,max_queue_size=None):
            if type(delay) is type(0): print("error: delay's type is int")

            cmds = []
            netemargs = '%s%s%s%s' % (
                'delay %s ' % delay if delay is not None else '',
                '%s ' % jitter if jitter is not None else '',
                'loss %.5f ' % loss if loss is not None else '',
                'limit %d' % max_queue_size if max_queue_size is not None
                else '' )
            handle = int(parent.split(":")[1])*1+1
            if netemargs:
                cmd = "tc qdisc add dev %s parent %s handle %d: netem "  % ( intf_name, parent, handle) + netemargs
                cmds.append(cmd)
            return cmds

        # get interfaces name of links "s1<->src",  "s1<->dst" on switch
        link = self.linksBetween(self.s1,peer1)[0]
        intf_name1, intf_name2 = "", ""
        if 's1' in link.intf1.name: intf_name1 = link.intf1.name
        else: intf_name1 = link.intf2.name
        link = self.linksBetween(self.s1,peer2)[0]
        if 's1' in link.intf1.name: intf_name2 = link.intf1.name
        else: intf_name2 = link.intf2.name

        # generate classids
        classid1,classid2 = "", ""
        link = self.linksBetween(self.s1,peer2)[0]
        if 's1' in link.intf1.name: classid1 = link.intf1.name
        else: classid1 = link.intf2.name
        # ethernet name of s1: s1-eth#
        classid1 = int(classid1[6:])
        link = self.linksBetween(self.s1,peer1)[0]
        if 's1' in link.intf1.name: classid2 = link.intf1.name
        else: classid2 = link.intf2.name
        # ethernet name of s1: s1-eth#
        classid2 = int(classid2[6:])

        # generate cmds
        tcoutput = self.s1.cmd("tc qdisc show dev %s" % intf_name1)
        if "priomap" in tcoutput or "noqueue" in tcoutput:
            output = self.s1.cmd("tc qdisc add dev %s root handle 1:0 htb" % intf_name1)
        tcoutput = self.s1.cmd("tc qdisc show dev %s" % intf_name2)
        if "priomap" in tcoutput or "noqueue" in tcoutput:
            output = self.s1.cmd("tc qdisc add dev %s root handle 1:0 htb" % intf_name2)

        # half delay on two links
        if delay:
            for i, ch in enumerate(delay):
                if not ch.isdigit(): break
            delay = str(float(delay[:i])/2)+delay[i:]
        cmds = []
        _cmds, parent = bw_cmds(intf_name1, classid1, ip_src=peer2.IP(), bw=bw)
        cmds+=_cmds
        _cmds = lat_cmds(parent=parent, intf_name=intf_name1, delay=delay,jitter=jitter,loss=loss, max_queue_size=max_queue_size)
        cmds+=_cmds
        tcoutput = self.s1.cmd("tc qdisc show dev %s" % intf_name2)
        if "noqueue" in tcoutput:
            output = self.s1.cmd("tc qdisc add dev %s root handle 1:0 htb" % intf_name2)
        _cmds, parent = bw_cmds(intf_name2, classid2, ip_src=peer1.IP(), bw=bw)
        cmds+=_cmds
        _cmds = lat_cmds(parent=parent, intf_name=intf_name2, delay=delay,jitter=jitter,loss=loss, max_queue_size=max_queue_size)
        cmds+=_cmds

        # execute cmds
        tcoutputs = [self.s1.cmd(cmd) for cmd in cmds]
        for i,output in enumerate(tcoutputs):
            if output != "":
                print cmds[i]
                print output

        # configure peer
        if flag:
            peer1.add_edge(peer2)

    def buildChainTopo(self):
        #add peer
        peers = self.chain_topo.peers
        for i in range(len(peers)):
            name = 'p%d'%i
            cpu = peers[name]['cpu']
            if peers[name]['cls'] == 'GoEthereum': self.add_peer(name,cls=GoEthereum,cpu=cpu)
        self.start()

        # start time dilation
        if self.tdf != 1:
            self.dilateEmulation(self.tdf)

        print '[%s] start peer'%asctime()

        #start peer
        for i in range(len(peers)):
            name = 'p%d'%i
            self.name_to_peer[name].start_node(**peers[name]['params'])
        #TODO: instead sleep by more smart way
        sleep(6)
        #add link
        print '[%s] add neighbors'%asctime()

        links = self.chain_topo.links
        for p1_name in (links):
            for p2_name in (links[p1_name]):
                p1 = self.name_to_peer[p1_name]
                p2 = self.name_to_peer[p2_name]

                delay,bw,loss,jitter,max_queue_size = links[p1_name][p2_name]['delay'],links[p1_name][p2_name]['bw'], links[p1_name][p2_name]['loss'],links[p1_name][p2_name]['jitter'], links[p1_name][p2_name]['max_queue_size']

                self.add_edge(p1,p2,delay=delay,bw=bw,loss=loss,jitter=jitter,max_queue_size=max_queue_size)

        # wait until all peer connected
        # may need to be more general, it's little specified to geth
        flag = True
        peers_neighbor_num = {}
        for p1_name in links:
            for p2_name in links[p1_name]:
                if not p1_name in peers_neighbor_num: peers_neighbor_num[p1_name]=0
                if not p2_name in peers_neighbor_num: peers_neighbor_num[p2_name]=0
                peers_neighbor_num[p1_name]+=1
                peers_neighbor_num[p2_name]+=1

        while flag:
            flag = False
            while peers_neighbor_num:
                p1_name = peers_neighbor_num.keys()[0]
                p1 = self.name_to_peer[p1_name]
                neighbor_num = peers_neighbor_num[p1_name]
                if p1.peer_count() !=neighbor_num:
                    flag = True
                    break
                else: peers_neighbor_num.pop(p1_name)
            sleep(3)

        log = []
        for p1_name in links:
            p1 = self.name_to_peer[p1_name]
            log.append(p1.peer_count())
        print '[%s] peers number:'%asctime(),log
        print '[%s] complete add neighbors'%asctime()

    def del_edge(self):
        # TODO: If we disconnected application level connection, is it necessary to remove network connections between two hosts?
        pass

    def stop(self,flag=True):
        if flag: self.stop_peers()
        super(MiniChain, self).stop()

    def start_peers(self,genesis_file,**params):
        for name in self.name_to_peer:
            peer = self.name_to_peer[name]
            peer.start_node(genesis=genesis_file,**params)

    def stop_peers(self):
        for name in self.name_to_peer:
            peer = self.name_to_peer[name]
            peer.stop_node()

    def restart_peers(self):
        for name in self.name_to_peer:
            peer = self.name_to_peer[name]
            peer.restart_node()

    def cmd_peers(self,command):
        msgs = {}
        for name in self.name_to_peer:
            peer = self.name_to_peer[name]
            _msg = peer.send_rpc_cmd(command)
            msgs[name] = _msg
        return msgs

    def get_peers(self): return self.name_to_peer.values()

if __name__=="__main__":
    '''
    1. create network
    2. add peers
    3. start network
    4. start nodes
    5. add channels/edges between node
    '''
    from chain_topo import Topo

    # full mesh topo
    print 'start define topo'
    topo = Topo()
    for i in range(2): topo.add_peer('GoEthereum',genesis="genesis.json",maxpeers=2)
    for i in range(2):
        for j in range(i+1,2):
            topo.add_link('p'+str(i),'p'+str(j),bw=100,delay="10ms")

    # start network
    net = MiniChain(chain_topo=topo)
    print "[%s] net start" % asctime()

    # count neighbor of peers
    counter = 0
    peers = net.get_peers()
    while counter>0:
        log = []
        for peer in peers:
            log.append(peer.peer_count())
        log.sort()
        print log
        sleep(10)
        counter-=10
    CLI(net)
    net.stop()
