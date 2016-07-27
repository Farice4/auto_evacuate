from auto_evacuates.novacheck.network.network import Net_Interface
from auto_evacuates.novacheck.service.service import get_service_status
from auto_evacuates.novacheck.service.service import novaservice_retry
from auto_evacuates.novacheck.ipmi.ipmi import get_ipmi_status as ipmi_check
from auto_evacuates.log import logger
from auto_evacuates.fence_agent import FENCE_NODES
from auto_evacuates.fence_agent import Fence

FENCE_NODE = FENCE_NODES


def manager():
    # ipmi_checks = ipmi_check()
    net_obj = Net_Interface()
    net_checks = net_obj.get_net_status()

    # get network  error list
    error_network_node = []
    for net_check in net_checks:
        # default network check return error data ,when network check right,
        # the return none define neterr_node save network check error
        # return data

        network_node = net_check['name']
        network_name = net_check['net_role']
        network_status = net_check['status']
        network_ip = net_check['addr']
        error_network_node.append(network_node)

        if network_node in FENCE_NODE:
            logger.info("%s has been fence status,do not execute network"
                        "retry check" % network_node)
        else:
            logger.error("%s %s status is: %s (%s)" %
                         (network_node, network_name,
                          network_status, network_ip))
            if not net_obj.network_retry(network_node, network_name):
                if network_name == 'br-storage':
                    role = "network"
                    node = network_node
                    name = network_name
                    fence = Fence()
                    fence.compute_fence(role, node, name)

    ser_checks = get_service_status()
    for ser_check in ser_checks:
        service_node = ser_check['node']
        service_type = ser_check['datatype']
        service_status = ser_check['status']

        # when compute node recovery, will remove node from
        # FENCE_NODES node name
        if service_node in FENCE_NODE:
            if (service_node not in error_network_node) and \
                    (service_status == "up"):
                FENCE_NODE.remove(service_node)

        if service_status == "up":
            logger.info("%s %s status is: up" % (service_node, service_type))
        elif service_status == "down" or service_status == "unknown":
            if service_node in FENCE_NODE:
                logger.info("%s %s status is: %s" % (service_node,
                                                     service_type,
                                                     service_status))
                logger.info("%s has been fence status, do not execute service"
                            "retry check" % service_node)
            else:
                logger.error("%s %s status is: %s" %
                             (service_node, service_type, service_status))
                if novaservice_retry(service_node, service_type):
                    logger.info("%s %s has auto recovery" % (service_node,
                                                             service_type))
