from credentials import get_nova_credentials_v2
from novaclient.client import Client as nova_Client
from log import logger


class NovaClient(object):
    def __init__(self):
        self.nova_credentials = get_nova_credentials_v2()
        self.novaclient = nova_Client(**self.nova_credentials)

    def nova_evacuate(self, instance_id, host=None,
                      on_shared_storage=True, password=None):
        """evacuate an instance
        """
        return self.novaclient.servers.evacuate(instance_id,
                                                host, on_shared_storage,
                                                password)

    def nova_list(self, node):
        """list all instances of wrong compute-node
        return:
        all instancs in wrong compute-node
        """
        search_opts = {}
        search_opts['host'] = node
        instance_list = self.novaclient.servers.list(search_opts=search_opts)
        instances = []
        if instance_list:
            for instance in instance_list:
                instances.append(instance.id)
        else:
            logger.warn("%s not found any instances" % node)
        return instances

    def nova_service_list(self, node, binary="nova-compute"):
        """list one nova service of one node you want
        default: nova-compute
        return (service status and state)
        """
        nova_compute = self.novaclient.services.list(host=node, binary=binary)
        return nova_compute[0].status, nova_compute[0].state

    def nova_service_disable(self, node, binary="nova-compute"):
        """disable one nova service of one node you want
        default: nova-compute
        """
        return self.novaclient.services.disable(host=node, binary=binary)

    def nova_service_enable(self, node, binary="nova-compute"):
        """enable one nova service of one node you want
        default: nova-compute
        """
        return self.novaclient.services.enable(host=node, binary=binary)

    def get_compute(self, binary="nova-compute"):
        try:
            services = self.novaclient.services.list(binary=binary)
        except self.novaclient.exceptions.Unauthorized:
            logger.warn("Failed to authenticate to Keystone")
        except Exception:
            logger.warn("Failed to query service")

        node_count = len(services)
        counter = 0
        node_name = []

        while counter < node_count:
            service = services[counter]
            node_name.append(service.host)
            counter += 1

        return services, node_name

    def service_status(self):
        services = self.get_compute()[0]
        count = len(services)
        counter = 0
        ser_status = []

        while counter < count:
            service = services[counter]
            ser_status.append({"node": service.host, "status": service.status,
                               "state": service.state})
            counter += 1
        return ser_status

NovaClientObj = NovaClient()
