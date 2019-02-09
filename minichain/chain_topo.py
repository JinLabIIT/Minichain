class Topo(object):
    '''
    Define topology by add_peer and add_link
    '''
    def __init__(self):
        self.peers = {}
        self.links = {}

    def add_peer(self,cls_type,cpu,**run_params):
        '''
        the name of host will be assigned automatically
        cls_type: String
        cls_type: the type of node
        run_params: dict
        run_params: parameters for start application
        '''
        host_name = 'p%d'%len(self.peers)
        self.peers[host_name]={}
        self.peers[host_name]['cls']=cls_type
        self.peers[host_name]['cpu']=cpu
        self.peers[host_name]['params'] = run_params
        return host_name

    def add_link(self, p1_name, p2_name, delay=None, bw=None, loss=None, jitter=None, max_queue_size=None):
        if not p1_name in self.links: self.links[p1_name] = {}
        if not p2_name in self.links[p1_name]: self.links[p1_name][p2_name] = {}
        self.links[p1_name][p2_name]['delay'] = delay
        self.links[p1_name][p2_name]['bw'] = bw
        self.links[p1_name][p2_name]['loss'] = loss
        self.links[p1_name][p2_name]['jitter'] = jitter
        self.links[p1_name][p2_name]['max_queue_size'] = max_queue_size

