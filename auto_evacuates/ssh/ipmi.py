from auto_evacuates.utils import ssh_connect
from auto_evacuates.log import logger

CMD = {"power_status": "racadm serveraction powerstatus",
       "power_on": "racadm serveraction powerup",
       "power_off": "racadm serveraction powerdown",
       }


class IPMIManager(object):
    def __init__(self, ipaddr, name=''):
        """name is compute hostname, command is ssh connect execute"""
        self.name = name
        self.ipaddr = ipaddr

    def is_power_on(self):
        """Use utils PublicTool ssh_connect get power status"""
        command = CMD['power_status']
        ret, stdout, stderr = ssh_connect(self.ipaddr, command)
        if 'ON' in stdout:
            logger.info("%s power status is: %s" % (self.ipaddr, 'ON'))
            return True
        elif 'OFF' in stdout:
            logger.info("%s power status is: %s" % (self.ipaddr, 'OFF'))
            return False

    def turn_power_on(self):
        """Use utils PublicTool ssh_connect turn on power"""
        command = CMD['power_on']
        ssh_connect(self.ipaddr, command)

    def turn_power_off(self):
        """Use utils PublicTool ssh_connect turn off power"""
        command = CMD['power_off']
        ssh_connect(self.ipaddr, command)
