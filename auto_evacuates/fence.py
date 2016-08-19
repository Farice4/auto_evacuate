import eventlet


class FenceOperation(object):
    """Please some fence op may be fail, for example, if there is somewrong
    for ipmi network, fence_node_for_() storage and fence_node_for_service()
    may be fail, so fence_node_for_xxx() API should return value of type
    boolean
    """
    def __init__(self, nova_compute_client):
        self.nova_compute_client = nova_compute_client

    def fence_node_for_ipmi(self, hostname):
        if self.nova_compute_client.is_node_enabled(hostname):
            self.nova_compute_client.disable_node(hostname)
            # TODO add a timeout for eventlet
        while self.nova_compute_client.is_node_up(hostname):
            eventlet.sleep(3)

    def fence_node_for_storage(self):
        pass

    def fence_node_for_service(self):
        pass
