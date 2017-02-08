import eventlet
eventlet.monkey_patch()
import commands
from auto_evacuates.log import logger
from auto_evacuates.config import CONF
from auto_evacuates.exception import SSHError, NovaClientError, ConsulError
from auto_evacuates.novacomputeclient import NovaComputeClient
from auto_evacuates.utils import ssh_connect, ele_filter
from auto_evacuates.Consul.check import NetworkManager
from auto_evacuates.Consul.record import FenceNodeManager
from auto_evacuates.ssh.ipmi import IPMIManager
from auto_evacuates.ssh.check import NetworkCheck
import re
import sys

IPMI_ADDR_FILE = CONF.get('idrac', 'file')
NOVACLIENT_AUTH = {'username': CONF.get('novaclient', 'username'),
                   'api_key': CONF.get('novaclient', 'api_key'),
                   'project_id': CONF.get('novaclient', 'project_id'),
                   'auth_url': CONF.get('novaclient', 'auth_url'),
                   'version': CONF.get('novaclient', 'version')}
STORAGE_IFNAME = CONF.get('ifname', 'storage')
MANAGE_IFNAME = CONF.get('ifname', 'manage')
NETWORK_CHECK = {
                 STORAGE_IFNAME:  {
                         'func_name': CONF.get('storage_network_check',
                                               'func_name'),
                         'port': int(CONF.get('storage_network_check',
                                              'port')),
                         },
                 MANAGE_IFNAME: None,
                 }
NET_TIME = {'interval': CONF.get('network_check', 'interval'),
            'timeout': CONF.get('network_check', 'timeout')}


class Manager(object):

    def __init__(self):
        self.compute_nodes = []
        self.nova_compute_client = NovaComputeClient(NOVACLIENT_AUTH)
        self.pool = eventlet.GreenPool()  # give a greenthread size?
        self.network_manager = {}
        self.fence_node_manager = None
        # consul server ip
        self.current_ip = None

    def _init_check(self):
        # 1.init node struct
        #   * {'hostname':'xxx', 'pxeaddr':'xxx', 'ipmiaddr': 'xxx'}
        def _get_remote_ip(ifname, pxe_ip):
            # get ip from all compute nodes by pxeaddr(ssh)
            command = ifname.join(["/sbin/ifconfig ",
                                   " |grep 'inet '|awk '/inet /{print $2}'"])
            ret, stdout, stderr = ssh_connect(pxe_ip, command)
            if stdout:
                return stdout.strip()
        try:
            with open(IPMI_ADDR_FILE) as f:
                for l in f.readlines():
                    p = re.compile(r'(.+):(.+):(.+):(.+):(.+):(.+)')
                    hostname, shortname, pxeaddr, roler, macaddr, ipmiaddr \
                        = p.match(l.strip('\n')).groups()
                    if 'compute' in roler:
                        item = {
                                'hostname': hostname,
                                'pxeaddr': pxeaddr,
                                'ipmimanager': IPMIManager(ipmiaddr,
                                                           hostname)
                                }
                        item[STORAGE_IFNAME] = _get_remote_ip(STORAGE_IFNAME,
                                                              pxeaddr)
                        item[MANAGE_IFNAME] = _get_remote_ip(MANAGE_IFNAME,
                                                             pxeaddr)
                        self.compute_nodes.append(item)
        except Exception as e:
            logger.error('Failed to init compute nodes: %s' % e)
            sys.exit(1)
        # 2.init network or service(storage datecenter) by consul
        #   need register check func by consul on leader
        #   * get ip from all compute nodes by pxeaddr(ssh)
        #   * according to ip and other params register check func
        #   * verify check can get true result as soon as possible
        # init network check
        self._init_net_check(STORAGE_IFNAME)
        # init service check
        # ex: self._init_service_check(STORAGE_IFNAME)
        # init fence_node(storage)
        compute_node_names = [node['hostname'] for node in self.compute_nodes]
        self.fence_node_manager = FenceNodeManager(self.current_ip,
                                                   compute_node_names)
        # 3.init network or service(mgmt datecenter) by consul
        # _init_net_check(MANAGER_IFNAME)
        # _init_service_check(MANAGER_IFNAME)
        # init fence_node(mgmt)
        # serive check
        # _init_service_check(MANAGER_IFNAME)

    def _init_net_check(self, ifname):
        def _get_current_ip(ifname):
            command = ifname.join(["/sbin/ifconfig ",
                                   " |grep 'inet '|awk '/inet /{print $2}'"])
            status, stdout = commands.getstatusoutput(command)
            return stdout
        self.current_ip = _get_current_ip(ifname)
        # for judge leader
        self.network_manager[ifname] = NetworkManager(self.current_ip)
        for compute_node in self.compute_nodes:
            # to do: eventlet?
            # register in consul server agent use current_ip,
            # register in consul client agent use compute_node['storage_ip']
            net_manager = NetworkManager(compute_node[ifname],
                                         NET_TIME)
            try:
                net_manager.set_network_check(compute_node[ifname],
                                              NETWORK_CHECK[ifname])
            except ConsulError as e:
                logger.error("ConsulError lead to register net "
                             "check on %s failed: %s"
                             % (compute_node['hostname'], e))
            except Exception as e:
                logger.error("Unknown Error lead to register net "
                             "check on %s failed: %s"
                             % (compute_node['hostname'], e))

    def _check_ipmi(self):
        err_nodes = []
        for node in self.compute_nodes:
            try:
                if not node['ipmimanager'].is_power_on():
                    err_nodes.append(node)
            except SSHError as e:
                logger.error('SSH Error is: %s' % e)
            except Exception as e:
                logger.error('Unknown Error is: %s' % e)
        return self._update_fence_nodes(err_nodes)

    def _check_network(self, ifname):
        err_nodes_list = []
        empty_list = []
        err_nodes_by_ssh = None
        err_nodes_by_consul = None
        network_check = NetworkCheck(self.compute_nodes)
        try:
            err_nodes_by_ssh = network_check.get_network_check(ifname)
            if err_nodes_by_ssh:
                err_nodes_list.append(err_nodes_by_ssh)
            else:
                return self._update_fence_nodes(empty_list)
            network_manager = self.network_manager[ifname]
            err_nodes_by_consul = network_manager.get_network_check()
            if err_nodes_by_consul:
                err_nodes_list.append(err_nodes_by_consul)
            else:
                return self._update_fence_nodes(empty_list)
        except SSHError as e:
            logger.error('SSH Error is: %s' % e)
        except ConsulError as e:
            logger.error('ConsulError is: %s' % e)
        except Exception as e:
            logger.error('Unknown Error is: %s' % e)
        err_nodes = ele_filter(err_nodes_list)
        return self._update_fence_nodes(err_nodes)

    def _check_service(self):
        pass

    def _update_fence_nodes(self, err_nodes):
        try:
            # 1.when the currect node is record, remove it from record
            fence_nodes = self.fence_node_manager.get()
            correct_nodes = [n for n in fence_nodes if n not in err_nodes]
            if correct_nodes:
                logger.warn("%s has been up, remove from fence_node",
                            correct_nodes)
                for n in correct_nodes:
                    self.fence_node_manager.remove(n)
        except ConsulError as e:
            logger.warn("ConsulError lead to update fence nodes failed: %s"
                        % e)
        except Exception as e:
            logger.warn("Unknown Error lead to update fence nodes failed: %s"
                        % e)
        # 2.when error node isn't record, it's fence  and record
        return [n for n in err_nodes
                if n not in fence_nodes]

    def _fence_and_evacuate(self, err_node_dict):
        hostname = err_node_dict['hostname']
        ipmimanager = err_node_dict['ipmimanager']
        if not self.fence_node_manager.add(hostname):
            logger.error("fence_node: %s add failed!" % hostname)
            return
        try:
            # 1.fence by novaclient
            if self.nova_compute_client.is_node_enabled(hostname):
                self.nova_compute_client.disable_node(hostname)
            while self.nova_compute_client.is_node_up(hostname):
                eventlet.sleep(3)
            # 2.fence by ipmi
            if ipmimanager.is_power_on():
                ipmimanager.turn_power_off()
            while ipmimanager.is_power_up():
                eventlet.sleep(3)
            logger.warn("%s fence successed" % hostname)
            # 3.evacuate by nova
            if self.nova_compute_client.evacuate_all(hostname):
                logger.warn('evacuate instances from %s successed'
                            % hostname)
            else:
                if not self.fence_node_manager.remove(hostname):
                    logger.warn("fence_node: %s remove failed!" % hostname)
        except NovaClientError as e:
            logger.error("NovaClientError lead to fence %s failed:%s"
                         % (hostname, e))
            if not self.fence_node_manager.remove(hostname):
                logger.warn("fence_node: %s remove failed!" % hostname)
        except SSHError as e:
            logger.error("SSHError lead to fence %s failed:%s"
                         % (hostname, e))
        except Exception as e:
            logger.error("UnknownError lead to fence %s failed:%s"
                         % (hostname, e))
            if not self.fence_node_manager.remove(hostname):
                logger.warn("fence_node: %s remove failed!" % hostname)

    def _handle_nodes(self, err_nodes):
        err_node_dicts = []
        err_node_dict = {}
        for err_node in err_nodes:
            for compute_node in self.compute_nodes:
                if err_node == compute_node['hostname']:
                    err_node_dict['hostname'] = err_node
                    err_node_dict['ipmimanager'] = compute_node['ipmimanager']
            err_node_dicts.append(err_node_dict)
        self.pool.imap(self._fence_and_evacuate, err_node_dicts)

    def run(self):
        logger.info('start worker')
        # 1.init check
        # notice: update idrac file when remove or add node
        self._init_check()
        while True:
            try:
                # 2.judge this node is br-storage leader or not
                if self.network_manager[STORAGE_IFNAME].is_leader():
                    # 3.check ipmi, fence err nodes,evacuate instances
                    # only check by one leader
                    self.network_manager[STORAGE_IFNAME].init_consul()
                    self.fence_node_manager.init_consul()
                    ipmi_errs = self._check_ipmi()
                    if ipmi_errs:
                        self._handle_nodes(ipmi_errs)
                    # 4.check storage network,fence and evacuate instances
                    # *storage:fence err nodes,evacuae instances
                    store_net_errs = self._check_network(STORAGE_IFNAME)
                    if store_net_errs:
                        self._handle_nodes(store_net_errs)
                    # 5.send a email (the log of run one time )
                else:
                    logger.info("This node is not the leader,"
                                "no need to do any check")
            except Exception as e:
                logger.error("Unknown error: %s" % e)
            eventlet.sleep(30)
