import os
import socket
import json
from time import sleep

from mininet.log import error, info

from blockchain_node import BlockchainNode

class GoEthereum(BlockchainNode):

    '''
    Control GoEthereum clients
    '''
    def __init__(self, name, **params):
        self.genesis = None
        self.app_pid = None
        self.params = {}
        BlockchainNode.__init__(self,name, **params)

    def start_node(self,is_restart=False, **params):
        # restart without changing parameters
        if not is_restart:
            self.params = params
        # default setting. datadir; rpc; avoid disable ipc
        if not "datadir" in self.params:
            self.params["datadir"]="./.ether-"+self.name
        if not "rpc" in self.params:
            self.params["rpc"]=True
            #print("%s enable rpc"%self.name)
        if "ipcdisable" in self.params:
            self.params.pop("ipcdisable")
            #print("%s enable ipc"% self.name)
        # geth init if keystore is not found
        if not os.path.exists(self.params["datadir"]+"/keystore"):
            self.cmd("geth --datadir "+self.params["datadir"]+" init "+self.params.pop("genesis"))
            info('\n %s/keystore not found, run "geth init"...\n' % self.params["datadir"])

        # generate command
        start_cmd = "geth "
        for opt in self.params:
            if opt == "genesis": continue
            val = self.params[opt]
            if type(val)!=type(True):
                start_cmd+="--%s %s " % (opt, str(val))
            elif val==True:
                start_cmd+="--%s " % (opt)

        # execute command
        self.cmd("nohup "+start_cmd+" &> %s.log &"%self.name)
        i = 0
        while self.app_pid is None:
            msg = self.cmd("ps | grep geth")
            if msg:
                for pid in msg.split(" "):
                    if pid.isdigit(): self.app_pid = int(pid)
            i+=1
            sleep(0.1)
        if self.app_pid is None:
            error('\nstart ethereum node fail, start command: "%s"' % start_cmd)
            raise Exception("start ethereum fail")
        self.status = "RUN"
        info('\nstart ethereum node "%s" successfully. PID: %d\n' % (self.name, self.app_pid))

    def stop_node(self):
        if self.app_pid: self.cmd("kill %d" % self.app_pid)
        info('\nexit ethereum node "%s"' % self.name)
        self.app_pid = None
        self.status = "STOP"

    def restart_node(self):
        self.stop_node()
        self.start_node(is_restart=True)
        info('\nrestart ethereum node "%s" successfully. PID: %d\n' % (self.name, self.app_pid))
        print 'restart', self.app_pid
        self.status = "RUN"

    def send_rpc_cmd(self,rpc_cmd):
        """ Control geth clients by RPC """
        _socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_addr = self.params["datadir"]+'/geth.ipc'
        _counter = 0
        while not os.path.exists(server_addr) and _counter<100:
            _counter+=1
            sleep(0.1)
        try:
            _socket.connect(server_addr)
            _socket.sendall(rpc_cmd)
            res = b''
            BUFF_SIZE=1024
            while 1:
                part = _socket.recv(BUFF_SIZE)
                res+=part
                if len(part)<BUFF_SIZE:
                    break
            return res
        except socket.error, msg:
            print 'exist ipc file:', os.path.exists(server_addr), server_addr
            print self.name, 'status:', self.status
            error(self.name, msg, rpc_cmd)
        finally:
            #print "\nclosing %s socket\n" % self.name
            _socket.close()

    def add_edge(self, node):
        """ Add neighbor to peer """
        if self.status != "RUN": self.start_node()
        # get node address
        _msg = node.send_rpc_cmd('{"method":"admin_nodeInfo","id":1}')

        if _msg is None: return

        # change depends on rpc message
        msg = json.loads(_msg)
        node_addr = msg["result"]["enode"].split("@")[0]+'@'+node.IP()+':'+str(msg["result"]["ports"]["listener"])
        # len("enode://") == 8
        msg["result"]["enode"].split("@")[0][8:]

        # add node
        _msg = self.send_rpc_cmd('{"method":"admin_addPeer","params":["%s"],"id":1}' % node_addr)

    def del_edge(self, node):
        """ Remove neighbor from peer """
        if self.status != "RUN": self.start_node()
        # get node address
        _msg = node.send_rpc_cmd('{"method":"admin_nodeInfo","id":1}')

        if _msg is None: return

        # change depends on rpc message
        msg = json.loads(_msg)
        node_addr = msg["result"]["enode"].split("@")[0]+'@'+node.IP()+':'+str(msg["result"]["ports"]["listener"])

        # remove node
        _msg = self.send_rpc_cmd('{"method":"admin_removePeer", "params":["%s"], "id":1}' % node_addr)

    def new_account(self,passphrase=""):
        _msg = self.send_rpc_cmd('{"method": "personal_newAccount", "params": ["%s"], "id":1}' % passphrase)
        if _msg is None: return
        pub_key = json.loads(_msg)["result"]
        return pub_key

    def set_ether_base(self,address):
        """ address: public key address """
        _msg = self.send_rpc_cmd('{"method": "miner_setEtherbase", "params": ["%s"], "id":1}' % address)
        if _msg is None: return
        return json.loads(_msg)["result"]

    def miner_start(self, number=4):
        """number: thread number"""
        _msg = self.send_rpc_cmd('{"method": "miner_start", "params": [%d], "id":1}' % number)
        if _msg is None: return
        return json.loads(_msg)["result"]

    def miner_stop(self):
        _msg = self.send_rpc_cmd('{"method": "miner_stop", "params": [], "id":1}')
        if _msg is None: return
        return json.loads(_msg)["result"]

    def get_balance(self, address, params="latest"):
        """
        address: 20 Bytes - address to check for balance.
        params: integer block number, or the string "latest",
                "earliest" or "pending", see the default block parameter
        """
        _msg = self.send_rpc_cmd('{"method":"eth_getBalance","params":["%s", "%s"],"id":1}' % (address, params))
        if _msg is None: return
        return int(json.loads(_msg)["result"],16)

    def get_blockbynumber(self,number,full_tx=False):
        _msg = self.send_rpc_cmd('{"method":"eth_getBlockByNumber","params":["%s",%s], "id":1}'
                % (hex(number),str(full_tx).lower()))
        if _msg is None: return
        return json.loads(_msg)["result"]

    def get_difficulty(self,number):
        if number=="latest":
            number = self.block_number()
        _msg = self.get_blockbynumber(number)
        if _msg is None: return
        return int(_msg["difficulty"],16)

    def block_number(self):
        _msg = self.send_rpc_cmd('{"method":"eth_blockNumber","params":[],"id":1}')
        if _msg is None: return
        return int(json.loads(_msg)["result"],16)

    def peer_count(self):
        _msg = self.send_rpc_cmd('{"method":"net_peerCount","id":1}')
        if _msg is None: return
        return int(json.loads(_msg)["result"],16)

    def import_raw_key(self,keydata,passphrase):
        _msg = self.send_rpc_cmd('{"method":"personal_importRawKey", "params":["%s","%s"], "id":1}' % (keydata, passphrase))
        if _msg is None: return
        return json.loads(_msg)["result"]

    def unlock_account(self,pub_key,passphrase,duration):
        _msg = self.send_rpc_cmd('{"method":"personal_unlockAccount","params":["%s","%s",%d],"id":1}' % (pub_key, passphrase, duration))
        if _msg is None: return
        return json.loads(_msg)["result"]

    def new_tx(self, sender_key, receiver_key, amount_str, gas="", gas_price="", data=""):
        """
        sender_key: sender public key
        receiver_key: receiver public key
        amount_str: "NUMBER UNIT"
        unit: wei; Kwei; Mwei; Gwei; microether; milliether; ether
        """
        amount, unit = amount_str.split(" ")
        amount = float(amount)

        if unit=="Kwei" or unit=="babbage": amount*=10**3
        elif unit=="Mwei" or unit=="lovelace": amount*=10**6
        elif unit=="Gwei" or unit=="shannon": amount*=10**9
        elif unit=="microether" or unit=="szabo": amount*=10**12
        elif unit=="milliether" or unit=="finney": amount*=10**15
        elif unit=="ether": amount*=10**18

        tx = '{"from":"%s","to":"%s","value":"%s"' % (sender_key, receiver_key, hex(int(amount)))
        if len(gas): tx+=',"gas":"%s"'%gas
        if len(gas_price): tx+=',"gasPrice":"%s"'%gas_price
        if len(data): tx+=',"data":"%s"'%data
        tx+='}'
        return tx


    def send_transaction(self,tx, passphrase):
        _msg = self.send_rpc_cmd('{"method":"personal_sendTransaction","params":[%s, "%s"],"id":1}' % (tx, passphrase))
        if _msg is None: return
        print _msg
        return json.loads(_msg)["result"]

    def __del__(self):
        if self.app_pid!=None: self.stop_node()

if __name__=="__main__":
    from chain_net import MiniChain
    c = 0.1
    net = MiniChain()
    node = net.add_peer('e1', cls=GoEthereum,cpu=c)
    net.start()
    node.start_node(genesis="g2.json",verbosity=4)
    coin_base = node.new_account()
    node.set_ether_base(coin_base)
    node.miner_start(4)
    sleep(1200)
    node.miner_stop()
    if node.block_number()==0:
        print 'block interval: infi '
    else:
        print 'block interval: : ', 1200.0/node.block_number()
    print node.get_balance(coin_base)
    net.stop()
    print 'stop', node.status

