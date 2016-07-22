"""
Nova service check record all data
If nova service check get service false, the nova service will be execute nova
service-disable node, but do not execute evacuate.
"""
import commands
import time
from auto_evacuates.log import logger
from auto_evacuates.openstack_novaclient import NovaClientObj as nova_client
from auto_evacuates.fence_agent import Fence
from auto_evacuates.fence_agent import FENCE_NODES

FENCE_NODE = FENCE_NODES


class NovaService(object):

    def __init__(self):
        self.compute = nova_client.get_compute()[1]
        self.service = nova_client.get_compute()[0]

    def sys_compute(self):
        """use systemctl check openstack-nova-compute service message

        return: sys_com data format list
        """
        logger.info("openstack-nova-compute service start check")

        sys_com = []
        for i in self.compute:
            (s, o) = commands.getstatusoutput("ssh '%s' systemctl -a|grep \
                                                openstack-nova-compute" % (i))
            if s == 0 and o is not None:
                if 'running' in o and 'active' in o:
                    sys_com.append({"node": i, "status": "up",
                                    "datatype": "novacompute"})
                elif 'dead' in o and 'inactive' in o:
                    sys_com.append({"node": i, "status": "down",
                                    "datatype": "novacompute"})
                elif 'failed' in o:
                    sys_com.append({"node": i, "status": "down",
                                    "datatype": "novacompute"})
            else:
                sys_com.append({"node": i, "status": "unknown",
                                "datatype": "novacompute"})
                logger.warn("%s openstack-nova-compute service unknown" % i)

        return sys_com

    def ser_compute(self):
        """use novaclient check nova-compute status and state message

        novaclient get state all ways  time delay
        :return: ser_com data format list
        """
        logger.info("nova-compute status and state start check")

        ser_com = []
        services = self.service
        if not services:
            logger.warn("Service could not be found nova-compute")
        else:
            count = len(services)
            counter = 0
            while counter < count:
                service = services[counter]
                host = service.host
                if service.status == "enabled" and service.state == "up":
                    ser_com.append({"node": host, "status": "up",
                                    "datatype": "novaservice"})
                elif service.status == "disabled":
                    if service.binary == "nova-compute" and \
                            service.disabled_reason:
                        ser_com.append({"node": host, "status": "up",
                                        "datatype": "novaservice"})
                    ser_com.append({"node": host, "status": "down",
                                    "datatype": "novaservice"})
                elif service.state == "down":
                    ser_com.append({"node": host, "status": "down",
                                    "datatype": "novaservice"})
                else:
                    logger.error("nova compute on host %s is in an "
                                 "unknown State" % (service.host))
                counter += 1

            return ser_com


def get_service_status():
    """ When manage get nova service check data ,will be return nova_status data

    :return: nova_status is a list data
    :Example: nova_status = [{"node":"node-1", "status":"up",
    "datatype":"novaservice"}, {"node":"node-2", "status":"down",
    "datatype":"novacompute"}]
    """

    nova_status = []
    ns = NovaService()
    for i in ns.sys_compute():
        nova_status.append(i)

    for n in ns.ser_compute():
        nova_status.append(n)

    return nova_status


def novaservice_retry(node, datatype):
    """If first check false, the check will retry three times

    """
    ns = NovaService()
    fence = Fence()
    role = "service"

    if datatype == "novaservice":
        for i in range(3):
            logger.warn("%s %s start retry %d check" % (node, datatype, i+1))
            status = ns.ser_compute()
            time.sleep(10)

        for n in status:
            # Execute three times after,get status data, the data only the
            # third data.
            if "down" in n.values():
                fence.compute_fence(role, node)

    elif datatype == "novacompute":
        for i in range(3):
            logger.warn("%s %s start retry %d check" % (node, datatype, i+1))
            status = ns.sys_compute()
            time.sleep(10)

        for n in status:
            if "down" in n.values():
                fence.compute_fence(role, node)