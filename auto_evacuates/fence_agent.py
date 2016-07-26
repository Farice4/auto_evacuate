import time
from log import logger
from openstack_novaclient import NovaClientObj as nova_client
from novacheck.service.service import ServiceManage
from send_email import Email
# from novacheck.ipmi.ipmi import power_off


class Fence(object):
    def __init__(self):
        self.server_manage = ServiceManage()

    def fence_node(self, role, node, name):
        """when compute br-storage has down, will be execute
       openstack-nova-compute stop, nova-service disable,
       when openstack-nova-compute has stop, will be execute
       nova-service disable
       """
        if role == "network":
            self.server_manage.stop_nova_compute(node)
            if not self._nova_service_status(node):
                nova_client.nova_service_disable(node)
                while True:
                    service_down = self._nova_service_status(node)
                    if service_down:
                        message = "%s service %s had been error "\
                                  % (node, name)
                        email = Email()
                        email.send_email(message)
                        logger.info("send email with %s had been evacuated"
                                    % node)
                        return True
                    time.sleep(10)

        elif role == "service":
            self.server_manage.stop_nova_compute(node)
            if not self._nova_service_status(node):
                nova_client.nova_service_disable(node)
                message = "%s service %s had been error " % (node, name)
                email = Email()
                email.send_email(message)
                logger.info("send email with %s service %s had been error"
                            % (node, name))

    def _nova_service_status(self, node):
        """When execute evacuate, you must get service-list status disabled
        state down
        """
        service_status = nova_client.service_status()
        if service_status:
            for i in service_status:
                if node == i["node"]:
                    if i["status"] == "disabled" and i["state"] == "down":
                        # when execut vm_evacuate , must exec nova service
                        # check get nova service
                        # status and state
                        logger.warn("%s has error, the instance will"
                                    "evacuate" % node)
                        return True
