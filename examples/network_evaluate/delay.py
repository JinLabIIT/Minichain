import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from time import asctime,sleep
import os

from minichain.chain_topo import Topo
from minichain.chain_net import MiniChain


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def parse_log(filename):
    log = open(filename, 'r')
    lines = log.readlines()
    res = []
    if len(lines)>0 and '=' in lines[-1] and '/' in lines[-1]:
        for part in lines[-1].split('=')[1].split('/'):
            if isfloat(part): res.append(float(part))
        return res
    else: return -1

def generator(n, test_name):
    # full mesh topo
    print '[%s] start define topo: n='%asctime(),n
    topo = Topo()
    for i in range(n): topo.add_peer('GoEthereum',cpu=1./n, genesis="genesis.json",maxpeers=n, verbosity=5,nodiscover=True)
    for i in range(n):
        for j in range(i+1,n):
            if test_name=='base' or test_name=='ether':
                topo.add_link('p'+str(i),'p'+str(j))
            elif test_name=='ether_fixed_delay_1':
                delay = '1ms'
                topo.add_link('p'+str(i),'p'+str(j),delay=delay)
            elif test_name=='ether_fixed_delay_20' or test_name=='ether_miner':
                delay = '20ms'
                topo.add_link('p'+str(i),'p'+str(j),delay=delay)
            elif test_name=='ether_fixed_delay_600':
                delay = '600ms'
                topo.add_link('p'+str(i),'p'+str(j),delay=delay, max_queue_size=10)
            elif test_name=='ether_diff_delay':
                delay = str((i+1)*10+j)+'ms'
                topo.add_link('p'+str(i),'p'+str(j),delay=delay)
            else:
                print '!!! unkown test !!!'

    # start network
    net = MiniChain(chain_topo=topo)


    if test_name=='base':
        print 'stop peers'
        net.stop_peers()

    print "[%s] net is running" % asctime()
    return net

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def pingall(net, test_name, run_time, seq):
    print "[%s] test begin"%asctime()

    peers = net.get_peers()

    if test_name=='ether_miner':
        # half peers will be miner
        for i, peer in enumerate(peers):
            if i%2==0:
                peer.new_account()
                peer.miner_start()

    for i in range(len(peers)):
        for j in range(len(peers)):
            if i==j: continue
            create_directory('delay/%s/%d/'%(test_name, seq))
            peers[i].cmd('ping %s -i 1 -c %d  > delay/%s/%d/log_%s-%s &'
                    % (peers[j].IP(), run_time, test_name, seq, peers[i].name, peers[j].name))

    sleep(run_time+min(60,seq*4))
    net.stop()

    print "[%s] test stop \n\n" % asctime()

def plot(test_name, run_time, box=False):
    print '[%s] plot'%asctime()
    data = []
    peer_num = 2

    while peer_num<64:
        line = []
        for i in range(peer_num):
            for j in range(i+1,peer_num):
                    # set delay
                    if test_name in ['base', 'ether']: delay = 0
                    elif test_name=='ether_fixed_delay_1': delay = 1
                    elif test_name in ['ether_miner', 'ether_fixed_delay_20']: delay = 20
                    elif test_name=='ether_fixed_delay_600': delay = 600
                    elif test_name=='ether_diff_delay':
                            delay = (i+1)*10+j

                    # get data from log
                    filename = 'delay/%s/%d/log_p%d-p%d'%(test_name, peer_num, i, j)
                    res = parse_log(filename)
                    if res!=-1:
                        line.append((res[1]-delay))
                    else: print filename, 'is invalid'
                    filename = 'delay/%s/%d/log_p%s-p%s'%(test_name, peer_num, j, i)
                    res = parse_log(filename)
                    if res!=-1:
                        line.append((res[1]-delay))
                    else: print filename, 'is invalid'
        data.append(line)
        print test_name, peer_num, max(line), min(line)
        peer_num*=2

    plt.rcParams.update({'font.size': 22})
    axes = plt.gca()
    axes.set_ylim([0.02,0.2])
    axes.set_aspect(10)

    N=6
    ind = np.arange(N)
    plt.ylabel(u'\u0394D  (ms)')
    plt.xlabel('Number of hosts')
    plt.grid()

    if not box:
        plt.violinplot(data,showmeans=True)
        plt.xticks(ind, ('','2', '4', '8', '16', '32'))
        i=0
        while i<5:
            plt.text(i+1+0.1,sum(data[i])/len(data[i]),'%.2f'%(sum(data[i])/len(data[i])))
            i+=1
        plt.savefig('delay/results/%s_violin.pdf'%test_name,bbox_inches='tight')
        plt.clf()
    else:
        plt.boxplot(data,showmeans=True)
        plt.xticks(ind, ('0', '2', '4', '8', '16', '32'))
        i=0
        while i<5:
            plt.text(i+1+0.1,sum(data[i])/len(data[i]),'%.2f'%(sum(data[i])/len(data[i])))
            i+=1
        create_directory('delay/results')
        plt.savefig('delay/results/%s_box.pdf'%test_name,bbox_inches='tight')
        plt.clf()

def test(test_name,run_time):
    print '[%s] [delay test][%s] from 2 peer to 32 peer %dsec' % (asctime(), test_name, run_time)
    i=2
    while i<64:
        net = generator(i, test_name)
        pingall(net, test_name, run_time, i)
        i*=2

if __name__=="__main__":
    tests = ['base', 'ether', 'ether_fixed_delay_1', 'ether_fixed_delay_20', 'ether_fixed_delay_600', 'ether_diff_delay', 'ether_miner']
    for test_name in tests:
        test(test_name,200)
        plot(test_name,200)
