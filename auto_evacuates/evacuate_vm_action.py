from openstack_novaclient import NovaClientObj as nova_client
from log import logger


class EvacuateVmAction():
    def __init__(self, node):
        self._node = node

    def run(self):
        instances = nova_client.nova_list(self._node)
        try:
            for instance in instances:
                logger.warn("%s server start evacuate" % instance)
                nova_client.nova_evacuate(instance)
        except Exception as e:
            logger.error(e)