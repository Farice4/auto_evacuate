from auto_evacuates.utils import ele_filter
from auto_evacuates.log import logger
import commands


class NetworkCheck(object):

    def __init__(self, compute_nodes, port='22'):
        self.compute_nodes = compute_nodes
        self.port = port

    def _check_by_ping(self, ip):
        command = 'ping -c 3 %s' % ip
        status, out = commands.getstatusoutput(command)
        if status == 0:
            return True
        else:
            return False

    def _check_by_telnet(self, ip, port):
        command = 'echo -e "\n"|telnet %s %s|grep Connected' % (ip, port)
        status, out = commands.getstatusoutput(command)
        if status == 0:
            return True
        else:
            return False

    def get_network_check(self, ifname):
        err_nodes_by_ping = []
        err_nodes_by_telnet = []
        err_nodes_list = []
        # to do:eventlet
        for compute_node in self.compute_nodes:
            if not self._check_by_ping(compute_node[ifname]):
                err_nodes_by_ping.append(compute_node['hostname'])
            else:
                logger.info("ping %s is ok" % compute_node[ifname])
            if not self._check_by_telnet(compute_node[ifname], self.port):
                err_nodes_by_telnet.append(compute_node['hostname'])
            else:
                logger.info("telnet %s %s is ok"
                            % (compute_node['hostname'], self.port))
        if err_nodes_by_ping and err_nodes_by_telnet:
            err_nodes_list.append(err_nodes_by_ping)
            err_nodes_list.append(err_nodes_by_telnet)
            return ele_filter(err_nodes_list)
        else:
            return None
