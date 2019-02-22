from time import sleep, asctime
import matplotlib.pyplot as plt
import os

from minichain.chain_topo import Topo
from minichain.chain_net import MiniChain

def full_mesh(n, cpus_usage, bw, delay, client='GoEthereum', loss=None):
    topo = Topo()
    for i in range(n):
        topo.add_peer(client,
                      cpu=cpus_usage[i],
                      genesis="genesis.json",
                      maxpeers=n,
                      verbosity=5,
                      nodiscover=True)
    for i in range(n):
        for j in range(i+1,n):
            topo.add_link('p%d'%i,'p%d'%j,bw=bw,delay=delay,loss=loss)
    return topo

def plot(miners_res, output):
    for i, sizes in enumerate(miners_res):
        plt.switch_backend('agg')
        labels = ['Miner %d'%j for j in range(1, len(sizes)+1)]
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('[1 day] block distribution')
        plt.axis('equal')
        plt.savefig('%s/%d.pdf'%(output, i+1),bbox_inches='tight')

def test1(topo, tdf,run_time, output='.'):
    print '[%s] [tdf: %f] [run_time: %d] 51 percent attack test' % (asctime(), tdf, run_time)
    net = MiniChain(chain_topo=topo, tdf=tdf)
    peers = net.get_peers()

    # start miner
    for i, peer in enumerate(peers):
        pub = '0x%s'%str(i+1).zfill(40)
        peer.set_ether_base(pub)
        peer.miner_start(20)

    sleep(run_time)

    # stop miner
    for peer in peers:
        peer.miner_stop()

    # analyze status
    block_lens = []
    for peer in peers: block_lens.append(peer.block_number())
    print 'block length:', block_lens

    avg_inv = []
    for i in range(101, block_lens[0]+1,100):
        t1 = peers[0].get_blockbynumber(i)['timestamp']
        t0 = peers[0].get_blockbynumber(i-100)['timestamp']
        avg_inv.append((int(t1,16)-int(t0,16))/100.0)
    print 'avg interval:', avg_inv


    _percent = lambda s: [float(val)/sum(s) for val in s]
    miners_res = []
    res_percent = []
    for i, peer in enumerate(peers):
        block_num = block_lens[i]
        log = [0]*len(peers)
        for j in range(1, block_num+1):
            miner_id = peer.get_blockbynumber(j)['miner']
            log[int(miner_id[2:])-1] +=1
        miners_res.append(log)
        res_percent.append(_percent(log))

    net.stop()

    fh = open('%s/%s'%(output,'res.txt'), 'w')
    fh.write(str(miners_res))
    fh.close()

    plot(miners_res, output)


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    n,cpus_usage,bw,delay, tdf, run_time = 6, [.3,.14,.14,.14,.14,.14], 10, '2ms', 1, 3600*80
    topo = full_mesh(n,cpus_usage, bw,delay)
    create_directory('results/res_1_2ms_80h')
    test1(topo, tdf, run_time, 'results/res_1_2ms_80h')

    n,cpus_usage,bw,delay, tdf, run_time = 6, [.3,.14,.14,.14,.14,.14], 10, '2ms', 0.1, 3600*8
    topo = full_mesh(n,cpus_usage, bw,delay)
    create_directory('results/res_10_2ms_8h')
    test1(topo, tdf, run_time, 'results/res_10_2ms_8h')

    n,cpus_usage,bw,delay, tdf, run_time = 6, [.45,.11,.11,.11,.11,.11], 10, '10ms', 1, 1100
    topo = full_mesh(n,cpus_usage, bw,delay)
    create_directory('results/res_1_10ms_1100s')
    test1(topo, tdf, run_time, 'results/res_1_10ms_1100s')

    n,cpus_usage,bw,delay, tdf, run_time = 6, [.45,.11,.11,.11,.11,.11], 10, '400ms', 1, 1100
    topo = full_mesh(n,cpus_usage, bw,delay)
    create_directory('results/res_1_400ms_1100s')
    test1(topo, tdf, run_time, 'results/res_1_400ms_1100s')

    n,cpus_usage,bw,delay, tdf, run_time = 6, [.45,.11,.11,.11,.11,.11], 100, '40ms', 0.1, 110
    topo = full_mesh(n,cpus_usage, bw,delay)
    create_directory('results/res_10_40ms_110s')
    test1(topo, tdf, run_time, 'results/res_10_40ms_110s')

