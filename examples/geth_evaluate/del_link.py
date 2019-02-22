from time import sleep
from minichain.chain_topo import Topo
from minichain.chain_net import MiniChain

topo = Topo()
topo.add_peer('GoEthereum', cpu=.5, genesis="genesis.json")
topo.add_peer('GoEthereum', cpu=.5, genesis="genesis.json")
topo.add_link('p0','p1')

net = MiniChain(chain_topo=topo)
peers = net.get_peers()

for i, peer in enumerate(peers):
    print peer.peer_count()

peers[0].del_edge(peers[1])
sleep(5)

for i, peer in enumerate(peers):
    print peer.peer_count()

net.stop()
