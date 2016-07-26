from pyghmi import exceptions as pyghmi_exception
from pyghmi.ipmi import command as ipmi_command
from auto_evacuates.log import logger
from auto_evacuates import exception
from ipmi_plugin import ipaddr_get


class IpmiPower(object):

    def __init__(self, ip, user, passwd):
        """
        :param ip: idrac lan enable after config ip address
        :param user: idrac username,dell default root user
        :param passwd: idrac root user password
        :return:
        """

        self.ip = None
        self.user = None
        self.passwd = None

    def _power_status(self):
        """Get the power status for this node.

        :returns: power state POWER_ON, POWER_OFF, or ERROR
        :raises: IPMIFailure when the auo evacuate ipmi call fails.
        """
        status = []

        try:
            ipmicmd = ipmi_command.Command(bmc=self.ip, userid=self.user,
                                           password=self.passwd)

            ret = ipmicmd.get_power()
        except pyghmi_exception.IpmiException as e:
            msg = ("IPMI get power state failed for node %(node)s"
                   "with the following error: %(error)s") % (self.ip, e)
            logger.error(msg)
            raise exception.IPMIFailure(msg)

        state = ret.get('powerstate')

        if state == 'on':
            status.append({"node": self.ip, "status": state})
            return status
        elif state == 'off':
            status.append({"node": self.ip, "status": state})
            return status
        else:
            logger.warn("IPMI get power state for node %s"
                        "returns the following details: %s" %
                        (self.ip, state))
            status.append({"node": self.ip, "status": state})
            return status

    def _power_off(self):
        """Trun the power off for this node.

        :return: power state POWER_OFF
        """

        msg = ("IPMI power off failed ofr node %(node)s with the"
               "following error: %(error)s")
        try:
            ipmicmd = ipmi_command.Command(bmc=self.ip, userid=self.user,
                                           password=self.passwd)
            ret = ipmicmd.set_power('off')
        except pyghmi_exception.IpmiException as e:
            error = msg % {'node': self.ip, 'error': e}
            logger.error(error)
            raise exception.IPMIFailure(error)

        # state = ret.get('powerstate')
        # if state == 'off':
        #    return state
        # else:
        #    error = ("bad response: %s") % ret
        #    logger.error(msg, {'node':self.ip, 'error':error})
        #    raise exception.PowerStateFailure(pstate=state)

    def _reboot(self):
        """Reboot this node.

        If the power is off, turn it on. if the power is on, reset it.
        """

        msg = ("IPMI power reboot failed for node %(node)s with the"
               "following error: %(error)s")
        try:
            ipmicmd = ipmi_command.Command(bmc=self.ip, userid=self.user,
                                           password=self.passwd)
            ret = ipmicmd.set_power('boot')
        except pyghmi_exception.IpmiException as e:
            error = msg % {'node': self.ip, 'error': e}
            logger.error(error)
            raise exception.IPMIFailure(error)

        # state = ret.get('powerstate')
        # if 'error' in ret:
        #    error = ("bad response: %s") % ret
        #    logger.error(msg, {'node':self.ip, 'error': error})
        #    raise exception.PowerStateFailure(pstate=state)

        # state = ret.get('powerstate')

        # return state

    def _power_on(self):
        """Trun the power on for this node.
        """

        msg = ("IPMI power on failed for node %(node)s with the"
               "following error: %(error)s")
        try:
            ipmicmd = ipmi_command.Command(bmc=self.ip, userid=self.user,
                                           password=self.passwd)
            ret = ipmicmd.set_power('on')
        except pyghmi_exception.IpmiException as e:
            error = msg % {'node': self.ip, 'error': e}
            logger.error(error)
            raise exception.IPMIFailure(error)

        # state = ret.get('powerstate')
        # if state == 'on':
        #    return state
        # else:
        #    error = ("bad response: %s") % ret
        #    logger.error(msg, {'node':self.ip, 'error': error})
        #    raise exception.PowerStateFailure(pstate=state)


class IpmiManage(object):
    """Use IpmiManage class manage extenal schedule"""
    def __init__(self, user, passwd):
        """init IpmiPower class"""
        # self.ip = self.get_ip()
        self.user = user
        self.passwd = passwd
        self.power = IpmiPower(self.node, self.user, self.passwd)

    def power_status(self):
        """auto evacuate check node power status"""
        for ip in self.get_ip():
            self.power._power_status(ip, self.user, self.passwd)

    def power_off(self, node):
        """power_off shutdown faild node, Use Ipmi_Power function _power_off
        faild node transfer a faild node name, use power off or system init 0
        """
        pass

    def get_ip(self):
        """Use ipaddr_get function get idrac ip address"""
        ipaddr = []
        ip = ipaddr_get()
        for i in ip:
            name = i['nodename']
            ipaddr.append(i['ip'])

        return ipaddr
