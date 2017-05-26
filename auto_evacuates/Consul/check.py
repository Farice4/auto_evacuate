from auto_evacuates.Consul.consul_api import ConsulAPI
from auto_evacuates.utils import ele_filter
from auto_evacuates.log import logger


class NetworkManager(ConsulAPI):

    SYMBOL = 'netcheck'

    def __init__(self, current_ip, all_nodes, params=None):
        # consul server agent don't need register, params = None
        if params:
            self.interval = params['interval']
            self.timeout = params['timeout']
        self.current_ip = current_ip
        self.all_nodes = all_nodes

    def _set_ping(self, ip):
        return ip.join(['ping -c 3 ', ' >/dev/null'])

    def _get_check_names(self, check_intro):
        check_names = {}
        for flag in ConsulAPI.CHECK_FLAGS.keys():
            check_info = '_'.join([NetworkManager.SYMBOL,
                                   ConsulAPI.CHECK_FLAGS[flag]])
            name = ":".join([check_info, check_intro])
            check_names[flag] = name
        return check_names

    def set_network_check(self, ip, params):
        check_intro = ' '.join([params['func_name'], ip])
        check_names = self._get_check_names(check_intro)
        # register script
        script = self._set_ping(ip)
        if self.register_script(check_names['script'],
                                self.current_ip,
                                script):
            logger.info('register script_check to check %s success' % ip)
        else:
            logger.warn('register script_check to check %s failed' % ip)
        # register tcp
        if self.register_tcp(check_names['tcp'],
                             self.current_ip,
                             ip,
                             params['port']):
            logger.info("register tcp_check to check %s:%s success"
                        % (ip, params['port']))
        else:
            logger.warn('register tcp_check to check %s:%s failed'
                        % (ip, params['port']))

    def get_network_check(self, state=ConsulAPI.CHECK_STATES['error']):
        online_nodes = self.get_check_result('any')
        online_hosts = [n['Node'] for n in online_nodes]
        leave_nodes = [n for n in self.all_nodes if n not in online_hosts]
        err_nodes = self.get_check_result(state)
        # 1. divid err_nodes by check flags
        err_nodes_by_self = []
        err_nodes_by_script = []
        err_nodes_by_tcp = []
        err_nodes_list = []
        for err_node in err_nodes:
            # consul default check
            if err_node['CheckID'] == 'serfHealth':
                err_nodes_by_self.append(err_node['Node'])
                continue
            check_info = err_node['Name'].split(':')[0]
            symbol, flag = check_info.split('_')
            if symbol == NetworkManager.SYMBOL:
                if flag == ConsulAPI.CHECK_FLAGS['script']:
                    err_nodes_by_script.append(err_node['Node'])
                elif flag == ConsulAPI.CHECK_FLAGS['tcp']:
                    err_nodes_by_tcp.append(err_node['Node'])
                else:
                    logger.info("net check on %s is ok" % err_node['Node'])
        # the node which in leave status is error
        result = leave_nodes
        # 2.filter err_node which isn't found other checks
        # if the check by self is error, need't filter
        if err_nodes_by_self:
            result += err_nodes_by_self
        if err_nodes_by_script and err_nodes_by_tcp:
            err_nodes_list.append(err_nodes_by_script)
            err_nodes_list.append(err_nodes_by_tcp)
            result += ele_filter(err_nodes_list)
        return result


class ServiceManager(ConsulAPI):
    pass
