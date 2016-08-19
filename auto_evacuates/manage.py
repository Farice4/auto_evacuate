import eventlet
eventlet.monkey_patch()
from auto_evacuates.consul_api import is_leader
from auto_evacuates.log import logger
from auto_evacuates.config import CONF
from auto_evacuates.exception import IPMIError, NovaClientError
from auto_evacuates.ipmi import IPMIManager
from auto_evacuates.fence import FenceOperation
from auto_evacuates.novacomputeclient import NovaComputeClient
import re
import sys

IPMI_ADDR_FILE = CONF.get('idrac', 'file')
NOVACLIENT_AUTH = {'username': CONF.get('novaclient', 'username'),
                   'api_key': CONF.get('novaclient', 'api_key'),
                   'project_id': CONF.get('novaclient', 'project_id'),
                   'auth_url': CONF.get('novaclient', 'auth_url'),
                   'version': CONF.get('novaclient', 'version')}
# fake enum implementaion
FENCE_TYPE_POWER, FENCE_TYPE_NETWORK, FENCE_TYPE_SERVICE = range(3)


class FencedNode(object):
    def __init__(self):
        # TODO:get from rabbitmq
        self.power = set()
        self.network = set()
        self.service = set()

    def _find(self, type):
        if type == FENCE_TYPE_POWER:
            return self.power
        elif type == FENCE_TYPE_NETWORK:
            return self.network
        elif type == FENCE_TYPE_SERVICE:
            return self.service

    def remove(self, nodes, type):
        obj = self._find(type)
        for n in nodes:
            try:
                obj.remove(n)
            except KeyError:
                logger.warn('type %s no such node: %s', type, n)

    def add(self, nodes, type):
        obj = self._find(type)
        for n in nodes:
            obj.add(n)

    def remove_one(self, node, type):
        obj = self._find(type)
        try:
            obj.remove(node)
        except KeyError:
            logger.warn('type %s no such node: %s', type, node)

    def add_one(self, node, type):
        obj = self._find(type)
        obj.add(node)

    def get(self, type):
        obj = self._find(type)
        return list(obj)


class Manager(object):
    def __init__(self):
        self.ipmi_objs = []
        self.fenced_node = FencedNode()
        self.nova_compute_client = NovaComputeClient(NOVACLIENT_AUTH)
        self.fence_op = FenceOperation(self.nova_compute_client)
        self.pool = eventlet.GreenPool()  # give a greenthread size?

    def run(self):
        """check cluster status every 30s, if some serious error
        occurred, _handle_xxx_error() will handle them"""
        logger.info("start worker")
        self._init_ipmi(IPMI_ADDR_FILE)
        while True:
            try:
                if is_leader():
                    logger.debug("Start checking IPMI")
                    # TODO: add some comment about error_nodes
                    error_nodes = self._check_ipmi()
                    if error_nodes:
                        self._handle_ipmi_error(error_nodes)

                    logger.debug("Start checking network")
                    error_nodes = self._check_network()
                    if error_nodes:
                        self._handle_network_error(error_nodes)

                    logger.debug("Start checking service")
                    error_nodes = self._check_service()
                    if error_nodes:
                        self._handle_service_error(error_nodes)
                else:
                    logger.info("This node is not the leader,"
                                "no need to do any check")
                # TODO, send email?
            except Exception as e:
                # TODO, catch speical exception, raise unknow excep to caller?
                logger.error("Failed to auto evacuate: %s" % e)
            eventlet.sleep(30)

    def _update_fence_and_error_node(self, type, error_nodes):
        """
        This function do following things:
        - remove nodes from FENCE_NODE that are not in the error_nodes
        - update error_nodes: if nodes are in FENCE_NODE, no need to
           handle them
        @return error_nodes that contains error nodes which are not in
                FENCE_NODE
        """
        # update FENCE_NODE
        error_node_names = [n['hostname'] for n in error_nodes]
        correct_nodes = [n for n in self.fenced_node.get(type)
                         if n not in error_node_names]
        if correct_nodes:
            logger.warn('%s has been up, remove from fenced_node',
                        correct_nodes)
            self.fenced_node.remove(correct_nodes, type)

        # update error_nodes
        return [n for n in error_nodes
                if n['hostname'] not in self.fenced_node.get(type)]

    def _init_ipmi(self, conf):
        """ ipmi_objs = [
            {
                'hostname':'node-17.eayun.com',
                'shortname':'node-17',
                'macaddr':'xxxx',
                'pxeaddr': 'xxxxx',
                'ipmiaddr':'xxxx',
                'manager':IPMIManager(ipmiaddr)
            },
            {
                // other node
            }
        ]
        """
        try:
            with open(conf) as f:
                for l in f.readlines():
                    p = re.compile(r'(.+):(.+):(.+):(.+):(.+):(.+)')
                    hostname, shortname, pxeaddr, roler, macaddr, ipmiaddr \
                        = p.match(l.strip('\n')).groups()
                    if roler == 'compute':
                        item = {
                            'hostname': hostname,
                            'shortname': shortname,
                            'macaddr': macaddr,
                            'pxeaddr': pxeaddr,
                            'ipmiaddr': ipmiaddr,
                            'manager': IPMIManager(ipmiaddr, hostname)
                        }
                        self.ipmi_objs.append(item)
        except Exception as e:
            logger.error('Failed to init ipmi module from ipmi file: %s', e)
            sys.exit(1)

    def _check_ipmi(self):
        """check ipmi power status"""
        error_nodes = []
        try:
            for i in self.ipmi_objs:
                if not i['manager'].is_power_on():
                    error_nodes.append(i)
        except IPMIError as e:
            logger.error("IPMI Error is: %s" % e)
        except Exception as e:
            logger.error("Unknown Error %s" % e)
        finally:
            return self._update_fence_and_error_node(FENCE_TYPE_POWER,
                                                     error_nodes)

    def _handle_ipmi_error(self, error_nodes):
        self.pool.imap(self._handle_ipmi_one, error_nodes)

    def _handle_ipmi_one(self, node):
        # TODO: ensure power is off again
        self.fenced_node.add_one(node['hostname'], FENCE_TYPE_POWER)
        try:
            self.fence_op.fence_node_for_ipmi(node['hostname'])
            logger.info("%s fence successed" % node['hostname'])
        except NovaClientError as e:
            logger.error("NovaClientError lead to fence %s failed:%s"
                         % (node['hostname'], e))
            self.fenced_node.remove_one(node['hostname'], FENCE_TYPE_POWER)
        except Exception as e:
            logger.error("UnknownError lead to fence %s failed:%s"
                         % (node['hostname'], e))
            self.fenced_node.remove_one(node['hostname'], FENCE_TYPE_POWER)

        if self.nova_compute_client.evacuate_all(node['hostname']):
            logger.info('evacuate instances from %s successed'
                        % node['hostname'])
        else:
            self.fenced_node.remove_one(node['hostname'], FENCE_TYPE_POWER)

    def _check_network(self):
        return []

    def _handle_network_error(self, error_nodes):
        pass

    def _check_service(self):
        return []

    def _handle_service_error(self, service_checks):
        pass
