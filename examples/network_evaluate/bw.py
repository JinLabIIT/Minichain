import matplotlib
matplotlib.use('Agg')

import os
import subprocess
import matplotlib.pyplot as plt
import json
import numpy as np
from time import asctime,sleep

from minichain.chain_topo import Topo
from minichain.chain_net import MiniChain


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def parse_log(filename, protocol):
    if protocol=='udp':
        try:
            fh = open(filename, 'r')
            content = json.loads(fh.read().replace('-nan','0'))
            if 'intervals' in content and 'sum' in content['intervals'][0] and "bits_per_second" in content['intervals'][0]['sum']:
                return float(content['intervals'][0]['sum']['bits_per_second'])
        except:
            print 'invalid',filename
            return -1
    elif protocol=='tcp':
        try:
            fh = open(filename, 'r')
            content = json.loads(fh.read().replace('-nan','0'))
            res = []
            if 'end' in content and 'sum_sent' in content['end'] and "bits_per_second" in content['end']['sum_sent']:
                res.append(float(content['end']['sum_sent']['bits_per_second']))
            if 'end' in content and 'sum_received' in content['end'] and "bits_per_second" in content['end']['sum_received']:
                res.append(float(content['end']['sum_received']['bits_per_second']))
            else: return -1
            return res
        except:
            print 'invalid',filename
            return -1


def generator(n, test_name):
    # full mesh topo
    print 'start define topo: n=',n
    topo = Topo()
    for i in range(n): topo.add_peer('GoEthereum',cpu=1./n, genesis="genesis.json",maxpeers=n, verbosity=3,nodiscover=True)
    for i in range(n):
        for j in range(i+1,n):
            if '10M' in test_name:
                topo.add_link('p'+str(i),'p'+str(j))
            elif '100M' in test_name:
                topo.add_link('p'+str(i),'p'+str(j),bw=100)
            elif '1000M' in test_name:
                topo.add_link('p'+str(i),'p'+str(j),bw=1000)
            else:
                print '!!! unkown test !!!'

    # start network
    net = MiniChain(chain_topo=topo)

    if 'base' in test_name: net.stop_peers()

    print "[%s] net start" % asctime()
    return net

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def _test(net, test_name, run_time, seq, protocol):
    peers = net.get_peers()

    if 'miner' in test_name:
        # half peers will be miner
        for i, peer in enumerate(peers):
            if i%2==0:
                peer.new_account()
                peer.miner_start()

    # Start iperf3 server
    for i in range(len(peers)):
        for j in range(len(peers)):
            if i==j: continue
            # iperf3 version: 3.0.11
            # lower version: '-1' flag is invalid
            # higher version: cannot parse bw correctly
            create_directory('bw/%s/%s/%d/' % (protocol, test_name, seq))
            peers[i].cmd('iperf3 -s -p %d -J -1 -i 0 > bw/%s/%s/%d/s_%s-%s &'
                    % (5000+j, protocol, test_name, seq, peers[i].name, peers[j].name))

    sleep(5)
    bw = 0
    if '10M' in test_name: bw = 10
    elif '100M' in test_name: bw = 100
    elif '1000M' in test_name: bw = 1000
    else: print '!!!! unknown bandwidth !!!!'

    # Start iperf3 client
    for i in range(len(peers)):
        for j in range(len(peers)):
            if i==j: continue
            if protocol=='udp':
                peers[j].cmd('iperf3 -c %s -u -b %dm -p %d -t %d -J -i 0 > bw/%s/%s/%d/c_%s-%s &'
                        % (peers[i].IP(), bw, 5000+j, run_time, protocol, test_name, seq, peers[i].name, peers[j].name))
            else:
                peers[j].cmd('iperf3 -c %s -b %dm -p %d -t %d -J -i 0 > bw/%s/%s/%d/c_%s-%s &'
                        % (peers[i].IP(), bw, 5000+j, run_time, protocol, test_name, seq, peers[i].name, peers[j].name))

    # wait test finish
    sleep(200)
    flag = True
    i = 0
    while flag or i>20:
        flag = False
        res = subprocess.check_output(["ps","-ea"])
        for l in res.split('\n'):
            if 'iperf3' in l:
                flag = True
                break
        sleep(5)
        i+=1

    net.stop()


def plot(test_name, run_time, protocol, box=False):
    servers = []
    clients = []
    peer_num = 2

    while peer_num<32:
        server = []
        client = []
        for i in range(peer_num):
            for j in range(peer_num):
                if i==j: continue
                # set bw
                if '10M' in test_name: bw=10**7
                elif '100M' in test_name: bw=10**8
                elif '1000M' in test_name: bw=10**9
                else: print 'cannot find bw'

                # get data from log
                if protocol=='udp':
                    filename = 'bw/%s/%s/%d/s_p%d-p%d'%(protocol, test_name, peer_num, i, j)
                    res = parse_log(filename, protocol)
                    if res!=-1:
                        server.append(-(res-bw)/10**6)
                    else: print filename, 'is invalid'

                    filename = 'bw/%s/%s/%d/c_p%s-p%s'%(protocol, test_name, peer_num, j, i)
                    res = parse_log(filename, protocol)
                    if res!=-1:
                        client.append(-(res-bw)/10**6)
                    else: print filename, 'is invalid'
                elif protocol=='tcp':
                    filename = 'bw/%s/%s/%d/s_p%d-p%d'%(protocol, test_name, peer_num, i, j)
                    res = parse_log(filename, protocol)
                    if res!=-1:
                        client.append(-(res[0]-bw)/10**6)
                        server.append(-(res[1]-bw)/10**6)
                    else: print filename, 'is invalid'

        servers.append(server)
        clients.append(client)
        peer_num*=2

    if len(servers)==0 or len(clients)==0:
        print('!!!! cannot plot !!!!')
        return -1

    N=5
    ind = np.arange(N)

    def _plot(data, protocol, pos, g_type):

        plt.rcParams.update({'font.size': 22})
        plt.rcParams['figure.figsize'] = (8.0, 4.0)

        if g_type=='box':
            plt.boxplot(data,showmeans=True)
        elif g_type=='violin':
            plt.violinplot(data,showmeans=True)

        plt.xticks(ind, ('', '2', '4', '8','16','32'))

        plt.ylabel(r'$\Delta \tau$  (Mbps)')
        plt.xlabel('Number of hosts')
        plt.grid()

        i=0
        while i<4:
            plt.text(i+1+0.1,sum(data[i])/len(data[i]),'%.3f'%(sum(data[i])/len(data[i])))
            i+=1

        create_directory('bw/%s/results/'%(protocol))
        plt.savefig('bw/%s/results/%s_%s_%s.png'%(protocol,pos, test_name, g_type),bbox_inches='tight',dpi=1000)
        plt.clf()


    if box:
        _plot(servers, protocol, 'server', 'box')
        _plot(clients, protocol, 'client', 'box')
    else:
        _plot(servers, protocol, 'server', 'violin')
        _plot(clients, protocol, 'client', 'violin')

def test(test_name,run_time,protocol):
    print '[%s] [bw %s test][%s] from 2 peer to 32 peer %dsec' % (asctime(), protocol, test_name, run_time)
    i=2
    while i<64:
        net = generator(i, test_name)
        _test(net, test_name, run_time, i, protocol)
        i*=2

if __name__=="__main__":
    tests = ['base_10M', 'fixed_bw_10M', 'fixed_bw_100M', 'fixed_bw_1000M', 'miner_10M']
    for test_name in tests:
        test(test_name,200, 'tcp')
        plot(test_name,200,'tcp')
        test(test_name,200, 'udp')
        plot(test_name,200,'udp')
