import time
import commands
from log import logger
from openstack_novaclient import NovaClientObj as nova_client
from evacuate_vm_action import EvacuateVmAction
from send_email import Email

FENCE_NODES = []


class Fence(object):

    def compute_fence(self, role, node):
        nova_client.nova_service_disable(node)
        commands.getoutput("ssh '%s' systemctl stop openstack-nova-compute"
                           % node)

        logger.warn("%s nova-compute service is disabled."
                    "Nova cloud not create instance in %s" % (node, node))

        # add Fence node to global FENCE_NODES list
        if node in FENCE_NODES:
            logger.info("%s has been fence status" % node)
        else:
            FENCE_NODES.append(node)

            if role == "network":
                while True:
                    service_down = self.nova_service_status_retry(node)
                    if service_down:
                        self.vm_evacuate(node)
                        message = "%s service %s had been error "\
                                  % (node, role)
                        email = Email()
                        email.send_email(message)
                        logger.info("send email with %s had been evacuated"
                                    % node)
                        break
                    else:
                        time.sleep(10)
                        self.nova_service_status_retry(node)

            else:
                message = "%s service %s had been error " % (node, role)
                email = Email()
                email.send_email(message)
                logger.info("send email with %s service %s had been error"
                            % (node, role))

    def compute_fence_recovery(self, node, name):
        # when the node reboot must enable nova-compute enable
        nova_client.nova_service_enable(node)
        logger.info("%s nova-compute service is enabled.")

    def vm_evacuate(self, node):
        """When execute fence after, the error node will be evacuate

        """
        nova_evacuate = EvacuateVmAction(node)
        nova_evacuate.run()

    def nova_service_status_retry(self, node):
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