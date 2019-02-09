from mininet.node import CPULimitedHost

class BlockchainNode(CPULimitedHost):
    """
    A BlockchainNode is a node that is running an Blockchain system.
    It's an abstract base class for a building, where the initializer
    specifies the steps needed, and the concrete subclasses implement
    these steps.
    """

    """
    TODO:
        1. measurement API
    """

    def __init__(self, name, **params):
        CPULimitedHost.__init__(self,name,**params)
        self.status="INIT"

    def start_node(self):
        raise NotImplementedError

    def stop_node(self):
        raise NotImplementedError

    def restart_node(self):
        raise NotImplementedError

    def add_edge(self):
        raise NotImplementedError

    def del_edge(self):
        raise NotImplementedError

    def send_rpc_cmd(self):
        raise NotImplementedError

    def __str__(self):
        return "blockchain node: %s\nstatus: %s" % (self.name, self.status)

if __name__=="__main__":
    obj = BlockchainNode("n1")
