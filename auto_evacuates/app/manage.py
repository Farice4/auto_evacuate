from auto_evacuates.novacheck.network import NetInterface
from auto_evacuates.novacheck.service import ServiceManage
from auto_evacuates.log import logger
from auto_evacuates.fence_agent import Fence
from auto_evacuates.evacuate_vm_action import EvacuateVmAction
import time

# Manage is very important moudle, the program all operation
# Use manage moudle  schedule

FENCE_NODE = {}
# FENCE_NODE use record has been fence node
# FENCE_NODE data format: FENCE_NODE = {'power':['node-17','node-18'],
# 'network': ['node-19'], 'service': ['node-20', 'node-21']}


class Manager(object):
    def __init__(self):
        self.net_obj = NetInterface()
        self.service_obj = ServiceManage()
        # TODO: ipmi check

    def run(self):
        """runing will be schedule program all"""

        while True:
            try:
                if self.net_obj.leader():
                    logger.info("Program start running, auto evacuate "
                                "start check")
                    logger.info("Auto evacuate running network check")
                    self.net_checks = self._check_network()
                    if self.net_checks:
                        self._handle_network_error(self.net_checks)

                    logger.info("Auto evacuate running service check")
                    self.service_checks = self._check_service()
                    if self.service_checks:
                        self._handle_service_error(self.service_checks)
                else:
                    logger.info("This node is not the leader,"
                                "no need to do any check")
            except Exception as e:
                # TODO, catch speical exception, raise unknow excep to caller?
                logger.error("Failed to auto evacuate: %s" % e)
            time.sleep(30)

    def _check_network(self):
        return self.net_obj.get_net_status()

    def _handle_network_error(self, net_checks):
        for net_check in self.net_checks:
            # default network check return error data ,
            # when network check  right,
            # the return none define neterr_node save network check error
            # return data
            network_node = net_check['name']
            network_name = net_check['net_role']
            network_status = net_check['status']
            network_ip = net_check['addr']
            # so network check right return none, must record network error
            # node message
            error_network_node = [net_check['name'] for net_check
                                  in self.net_checks]
            if 'network' in FENCE_NODE.keys() and network_node in \
                    FENCE_NODE.get('network'):
                if network_node in error_network_node:
                    logger.info("%s has been fence status,do not"
                                "execute network retry check"
                                % network_node)
                else:
                    # if error_network_node do not exist, network status
                    # is up, will remove FENCE_NODE record
                    self._fence_node_remove('network', network_node)
            else:
                logger.error("%s %s status is: %s (%s)" %
                             (network_node, network_name,
                              network_status, network_ip))
                logger.info("Start recover netowork")
                network_recover_result = self._recover_network(network_node,
                                                               network_name)
                if not network_recover_result:
                    logger.info("Network recovery faild, Start fence node")
                    fence_result = self._fence('network',
                                               network_node,
                                               network_name)
                    if fence_result:
                        self._fence_node_add(network_node, "network")
                        logger.info("Start evacuate instances from error node")
                        self._evacuate(network_node)
                    else:
                        logger.error("fence %s error" % network_node)
                else:
                    logger.info("%s %s has auto recovery" % (network_node,
                                                             network_name))

    def _check_service(self):
        return self.service_obj.get_service_status()

    def _handle_service_error(self, service_checks):
        for service_check in self.service_checks:
            service_node = service_check['node']
            service_type = service_check['datatype']
            service_status = service_check['status']
            if 'service' in FENCE_NODE.keys() and service_node in \
                    FENCE_NODE.get('service'):
                if service_status == 'down' or service_status == 'known':
                    logger.info("%s has been fence status,"
                                "do not execute service"
                                "retry check" % service_node)
                else:
                    # if service in FENCE_NODE, the service is recovery
                    # service is up, will remove FENCE_NODE record
                    self._fence_node_remove('service', service_node)
            else:
                if service_status == "up":
                    logger.info("%s %s status is: up" % (service_node,
                                                         service_type))
                elif service_status == "down" or service_status == "unknown":
                        logger.error("%s %s status is: %s" %
                                     (service_node,
                                      service_type,
                                      service_status))
                        service_recover_result = self._recover_service(
                            service_node, service_type)
                        if not service_recover_result:
                            logger.info("Service recovery faild,"
                                        "Start fence node")
                            fence_result = self._fence('service',
                                                       service_node,
                                                       service_type)
                            if fence_result:
                                self._fence_node_add(service_node, "service")
                            else:
                                logger.error("fence %s error" % service_node)

                        else:
                            logger.info("%s %s has auto recovery" %
                                        (service_node, service_type))

    def _recover_network(self, node, name):
        """
        include retry and recovey
        """
        flag = 0
        while flag < 3:
            retry_result = self.net_obj.network_confirm(node, name)
            if retry_result:
                return True
            flag = flag + 1
            time.sleep(10)

        if self.net_obj.network_recover(node, name):
            return True
        return False

    def _recover_service(self, node, datatype):
        """
        include retry
        """
        for i in range(3):
            retry_result = self.service_obj.retry_service(node, datatype)
            if retry_result:
                return True
            time.sleep(10)
        # service retry three time faild, will be execute recovery
        # service recovery, only execute openstack-nova-compute recovery
        if self.service_obj.recovery_service(node, datatype):
            return True
        return False

    def _fence(self, role, node, name):
        """Use fence_agent fence faild node"""
        fence = Fence()
        return fence.fence_node(role, node, name)

    def _evacuate(self, node):
        """when fence faild node finish, will be execute evacuate"""
        evacuate = EvacuateVmAction(node)
        evacuate.run()

    def _fence_node_remove(self, role, node):
        """remove node from FENCE_NODE"""
        if role in FENCE_NODE.keys():
            if node in FENCE_NODE[role]:
                FENCE_NODE[role].remove(node)
                if not FENCE_NODE[role]:
                    FENCE_NODE.pop(role)

    def _fence_node_add(self, node, role):
        """add node from FENCE_NODE"""
        if role in FENCE_NODE.keys():
            t = FENCE_NODE[role]
            t.append(node)
        else:
            FENCE_NODE[role] = [node]
