from auto_evacuates.Consul.consul_api import ConsulAPI


class FenceNodeManager(ConsulAPI):
    '''
     record struct like:
     {
            'node-1': '1',
            'node-2': None,
     }
    '''

    def __init__(self, current_ip, all_nodes):
        self.all_nodes = all_nodes
        self.current_ip = current_ip

    def remove(self, node):
        return self.put_kv(key=node,
                           value=None)

    def add(self, node):
        return self.put_kv(key=node,
                           value='1')

    def get(self):
        nodes = []
        for node in self.all_nodes:
            value = self.get_kv(key=node)
            if value:
                nodes.append(node)
        return nodes
