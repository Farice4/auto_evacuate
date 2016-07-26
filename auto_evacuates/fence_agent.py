import time
import commands
from log import logger
from openstack_novaclient import NovaClientObj as nova_client
from send_email import Email
# from novacheck.ipmi.ipmi import power_off

FENCE_NODES = []


class Fence(object):

    def compute_fence(self, role, node, name):
        if not self.nova_service_status(node):
            nova_client.nova_service_disable(node)
        commands.getoutput("ssh '%s' systemctl stop openstack-nova-compute"
                           % node)
        logger.warn("%s nova-compute service is disabled."
                    "Nova can not create instance in %s" % (node, node))

        # logger.warn("%s will be shutdown system" % node)
        # power_off()

        # add Fence node to global FENCE_NODES list
        if node in FENCE_NODES:
            logger.info("%s has been fence status" % node)
        else:
            FENCE_NODES.append(node)

            if role == "network":
                while True:
                    service_down = self.nova_service_status(node)
                    if service_down:
                        message = "%s service %s had been error "\
                                  % (node, name)
                        email = Email()
                        email.send_email(message)
                        logger.info("the %s of instances will be evacuated"
                                    % node)
                        return True
                    time.sleep(10)
            else:
                message = "%s service %s had been error " % (node, name)
                email = Email()
                email.send_email(message)
                logger.info("send email with %s service %s had been error"
                            % (node, name))

    def compute_fence_recovery(self, node):
        # when the node reboot must enable nova-compute enable
        nova_client.nova_service_enable(node)
        logger.info("%s nova-compute service is enabled.")

    def nova_service_status(self, node):
        """When execute evacuate, you must get service-list status disabled
        state down

        :return: True or False
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
                    else:
                        return False
