from novaclient.client import Client
from auto_evacuates.log import logger
from auto_evacuates.utils import try_except_novaclient
from auto_evacuates.exception import NovaClientError


class NovaComputeClient(object):

    SERVICE_ENABLE = 'enabled'
    SERVICE_UP = 'up'
    BINARY = 'nova-compute'
    INSTANCE_STATUS = ['ACTIVE', 'SHUTOFF']

    def __init__(self, auth):
        self.auth = auth

    def _get_nova_client(self):
        novaclient = Client(username=self.auth['username'],
                            api_key=self.auth['api_key'],
                            project_id=self.auth['project_id'],
                            auth_url=self.auth['auth_url'],
                            version=self.auth['version'])
        return novaclient

    @try_except_novaclient
    def _get_node_service(self, hostname):
        '''return class novaclient.v2.services.Service'''
        novaclient = self._get_nova_client()
        return novaclient.services.list(host=hostname, binary=self.BINARY)[0]

    @try_except_novaclient
    def _get_node_servers(self, hostname):
        novaclient = self._get_nova_client()
        search_opts = {}
        search_opts['host'] = hostname
        search_opts['all_tenants'] = 1
        instance_list = []
        for status in self.INSTANCE_STATUS:
            search_opts['status'] = status
            instance_list.extend(novaclient.servers.list(
                search_opts=search_opts))
        instances = []
        if instance_list:
            for instance in instance_list:
                instances.append(instance.id)
        return instances

    def is_node_enabled(self, hostname):
        nova_compute = self._get_node_service(hostname)
        if nova_compute.status == self.SERVICE_ENABLE:
            return True
        return False

    def is_node_up(self, hostname):
        nova_compute = self._get_node_service(hostname)
        if nova_compute.state == self.SERVICE_UP:
            return True
        return False

    @try_except_novaclient
    def disable_node(self, hostname):
        '''return class novaclient.v2.services.Service'''
        novaclient = self._get_nova_client()
        novaclient.services.disable(host=hostname, binary=self.BINARY)

    @try_except_novaclient
    def evacuate(self, instance):
        novaclient = self._get_nova_client()
        novaclient.servers.evacuate(instance,
                                    host=None,
                                    on_shared_storage=True,
                                    password=None)

    def evacuate_all(self, hostname):
        instances = self._get_node_servers(hostname)
        all_sucessful = True
        if instances:
            for instance in instances:
                try:
                    self.evacuate(instance)
                    logger.warn("%s instance has evacuate" % instance)
                except NovaClientError as e:
                    logger.error("NovaClientError lead to evacuate a"
                                 "instance from %s failed: %s" %
                                 (hostname, e))
                    all_sucessful = False
                except Exception as e:
                    logger.error("UnknownError lead to evacuate a"
                                 "instance from %s failed: %s" %
                                 (hostname, e))
                    all_sucessful = False
        else:
            logger.info("%s not found any instances,need't to evacuate"
                        % hostname)
        return all_sucessful
