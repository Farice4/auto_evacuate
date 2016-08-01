import commands
import consul
import socket
import fcntl
import struct
import time
from netaddr import IPNetwork, IPAddress
from auto_evacuates.log import logger
from auto_evacuates.send_email import Email


class Network(object):
    def __init__(self):
        self.mgmt_ip = None
        self.storage_ip = None
        self.IPNetwork_m = None
        self.IPNetwork_s = None
        self.addr_net = 'br-storage'
        self.addr_net = 'br-mgmt'

    @property
    def addr_net(self):
        pass

    @addr_net.setter
    def addr_net(self, ifname):
        """
        get local ip addr and ip network
        """
        (n, ipnetwork) = commands.getstatusoutput("LANG=C ip a show "
                                                  "%s | awk '/"
                                                  "inet /{ print $2 }'"
                                                  % ifname)
        if n != 0:
            logger.error("get the local IpNetwork false")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ipaddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                  0x8915,  # SIOCGIFADDR
                                  struct.pack('256s',
                                  ifname[:15]))[20:24])
        if ifname == 'br-storage':
            self.storage_ip = ipaddr
            self.IPNetwork_s = ipnetwork
        else:
            self.mgmt_ip = ipaddr
            self.IPNetwork_m = ipnetwork

    def server_network_status(self, network, dict_networks):
        """
        Traversal all networks , when someone error ,
        assignment to dict and append to list
        """

        dict_network = {}
        members = network.agent.members()
        for member in members:
            if member['Tags']['role'] == 'node':
                if member['Status'] != 1:
                    name = member['Name'].split('_')
                    dict_network['name'] = name[1]
                    dict_network['status'] = False
                    dict_network['addr'] = member['Addr']
                    dict_network['role'] = member['Tags']['role']
                    if (IPAddress(member['Addr'])
                            in IPNetwork(self.IPNetwork_m)):
                        dict_network['net_role'] = 'br-mgmt'
                    elif (IPAddress(member['Addr']) in
                          IPNetwork(self.IPNetwork_s)):
                        dict_network['net_role'] = u'br-storage'
                    logger.info("%s network %s is down" % (
                        member['Name'], dict_network['net_role']))
                    # append the dict of error-network
                    dict_networks.append(dict_network)
                else:
                    if (IPAddress(member['Addr']) in
                            IPNetwork(self.IPNetwork_m)):
                        net_role = 'br-mgmt'
                    elif (IPAddress(member['Addr']) in
                            IPNetwork(self.IPNetwork_s)):
                        net_role = 'br-storage'
                    logger.info("%s network %s is up" % (
                        member['Name'], net_role))


class NetInterface(object):
    def __init__(self):
        self.net_obj = Network()

    def network_confirm(self, node, name):
        """
        retry three times to confirm the network,
        if confirm the network had died return True ,else return False
        """

        if name == 'br-storage':
            network = consul.Consul(host=self.net_obj.storage_ip, port=8500)
        else:
            network = consul.Consul(host=self.net_obj.mgmt_ip, port=8500)
        t_members = network.agent.members()
        for t_member in t_members:
            if t_member['Name'] == node and t_member['Status'] != 1:
                time.sleep(10)
            elif (t_member['Name'] == node and
                    t_member['Status'] == 1):
                return True
        return False

    def network_recover(self, node, name):
        """
        try to restore the network ,if no carried out fence
        """

        # when searched one network error , sleep awhile
        # if it can restore auto
        if name == 'br-storage':
            commands.getstatusoutput("ssh %s ifdown %s" % (node, name))
            time.sleep(2)
            commands.getstatusoutput("ssh %s ifup %s" % (node, name))
            logger.info("try to recovery %s %s" % (node, name))
            time.sleep(30)
            check_networks = self.get_net_status()
            # todo: node_check(node,name)
            for check_net in check_networks:
                if (check_net['name'] == node and
                        check_net['net_role'] == 'br-storage'):
                    logger.error("%s %s recovery failed. "
                                 "Begin execute nova-compute "
                                 "service disable" % (node, name))
                    return False
            logger.info("%s %s recovery Success" % (node, name))
            return True
        else:
            message = "%s network %s had been error " % (node, name)
            email = Email()
            email.send_email(message)
            return True

    def get_net_status(self):
        """
        :return: list of error network
        """

        dict_networks = []
        logger.info("start network check")
        mgmt_consul = consul.Consul(host=self.net_obj.mgmt_ip, port=8500)
        storage_consul = consul.Consul(host=self.net_obj.storage_ip, port=8500)
        self.net_obj.server_network_status(mgmt_consul, dict_networks)
        self.net_obj.server_network_status(storage_consul, dict_networks)
        return dict_networks

    # return current  leader
    def leader(self):
        """
        return current  leader
        """

        storage_consul = consul.Consul(self.net_obj.storage_ip, 8500)
        try:
            if (storage_consul.status.leader() ==
                    (self.net_obj.storage_ip + ":8300")):
                return True
            else:
                return False
        except Exception as e:
            logger.info("can't get consul leader, the reason is: %s" % e)
