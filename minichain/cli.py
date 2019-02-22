"""
A simple command-line interface for Minichain
"""

from cmd import Cmd

class CLI(Cmd):
    "Simple command-line interface to monitor and control emulator"

    prompt = 'minichain> '
    intro = 'Welcome to the Minichain CLI.   Type help or ? to list commands.\n'

    def __init__(self, minichain):
        self.mc = minichain
        Cmd.__init__(self)
        self.run()

    def run(self):
        "customize cmdloop()"
        while True:
            try:
                self.cmdloop()
                break
            except KeyboardInterrupt:
                print "\nInterrupt\n"

    def do_nodes(self, arg):
        'show existing nodes'
        print self.mc.name_to_peer.keys()

    def do_links(self, arg):
        'show peer to peer connections'
        links = self.mc.chain_topo.links
        for n1_name in links:
            for n2_name in links[n1_name]:
                print n1_name, '<->', n2_name

    def do_peersCount(self, arg):
        'show the number of neighbors of every nodes'
        peers = self.mc.get_peers()
        for i, peer in enumerate(peers):
            print peer.name, ':', peer.peer_count()

    def do_blocknumber(self,arg):
        'show the height of chain on every node'
        peers = self.mc.get_peers()
        for i, peer in enumerate(peers):
            print peer.name, ':', peer.block_number()

    def do_getBlock(self, arg):
        'show the ith block of node\nexample: getBlock p1 0'
        name, block_id = arg.split(' ')
        block_id = int(block_id)
        if name in self.mc.name_to_peer:
            peer = self.mc.name_to_peer[name]
            print peer.get_blockbynumber(block_id)

    def do_delEdge(self, arg):
        'remove one edge between two nodes'
        p1_name, p2_name = arg.split(' ')
        links = self.mc.chain_topo.links
        if p1_name in links and p2_name in links[p1_name]:
            p1 = self.mc.name_to_peer[p1_name]
            p2 = self.mc.name_to_peer[p2_name]
            p1.del_edge(p2)
            links[p1_name].pop(p2_name)
        elif p2_name in links and p1_name in links[p2_name]:
            p1 = self.mc.name_to_peer[p1_name]
            p2 = self.mc.name_to_peer[p2_name]
            p1.del_edge(p2)
            links[p2_name].pop(p1_name)

    def do_mining(self, node_name):
        'one node start mining\nexample: mining p1'
        if node_name in self.mc.name_to_peer:
            peer = self.mc.name_to_peer[node_name]
            # create coinbase account if it doesn't exist
            if peer.get_coinbase()==-1:
                peer.new_account()
            peer.miner_start()

    def do_stopMining(self, node_name):
        'one node stop mining\nexample: stopMining p1'
        if node_name in self.mc.name_to_peer:
            peer = self.mc.name_to_peer[node_name]
            peer.miner_stop()

    def do_exit(self, arg):
        "Exit"
        return 'exited by user command'

    def do_quit(self, arg):
        "Exit"
        return self.do_exit(arg)

    def do_EOF(self, arg):
        "Exit"
        return self.do_exit(arg)

if __name__=="__main__":
    from minichain.chain_topo import Topo
    from minichain.chain_net import MiniChain

    topo = Topo()
    topo.add_peer('GoEthereum', cpu=.1, genesis="genesis.json")
    topo.add_peer('GoEthereum', cpu=.1, genesis="genesis.json")
    topo.add_peer('GoEthereum', cpu=.1, genesis="genesis.json")
    topo.add_link('p0','p1')
    topo.add_link('p2','p1')
    topo.add_link('p2','p0')

    net = MiniChain(chain_topo=topo)

    CLI(net)

    net.stop()
