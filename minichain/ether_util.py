import json

class ether_genesis(object):

    def __init__(self):
        self.log = {}
        self.log["alloc"] = {}
        self.log["config"] = {}

    def set_alloc(self,key,value):
        self.log["alloc"][key] = value

    def del_alloc(self,key):
        self.log["alloc"].pop(key)

    def set_config(self,key,value):
        self.log["config"][key] = value

    def del_config(self,key,value):
        self.log["config"].pop(key)

    def set_param(self,key,value):
        self.log[key] = value

    def __str__(self):
        return json.dumps(self.log)

if __name__=="__main__":
    g = ether_genesis()
    g.set_alloc("0x0000000000000000000000000000000000000001", {"balance":"100000"})
    g.set_alloc("0x0000000000000000000000000000000000000002", {"balance":"200000"})
    g.set_alloc("0x0000000000000000000000000000000000000003", {"balance":"300000"})
    g.set_config("chainId", 100)
    g.set_config("homesteadBlock",0)
    g.set_config("eip155Block",0)
    g.set_config("eip158Block",0)
    g.set_param("difficulty","10000")
    g.set_param("gasLimit","210000")
    print g
