import consul
from auto_evacuates.exception import ConsulError
from auto_evacuates.utils import try_except_consul


def register_filter(func):
    def wrapper(*args, **kwargs):
        consul_obj = consul.Consul(args[2], port=ConsulAPI.PORT)
        if args[1] in consul_obj.agent.checks().keys():
            return True
        else:
            return func(*args, **kwargs)
    return wrapper


class ConsulAPI(object):

    PORT = 8500
    CHECK_FLAGS = {'script': 'script',
                   'http': 'http',
                   'tcp': 'tcp',
                   'ttl': 'ttl'}
    CHECK_STATES = {'error': 'critical',
                    'warning': 'warning',
                    'pass': 'passing',
                    'unknown': 'unknown',
                    'all': 'any'}

    @try_except_consul
    def is_leader(self):
        """
        return if this node is consule leader or not
        """
        consul_obj = consul.Consul(self.current_ip, port=ConsulAPI.PORT)
        leader = consul_obj.status.leader()
        if not leader:
            raise ConsulError("can't select leader!")
        if (self.current_ip in leader):
            return True
        else:
            return False

    @try_except_consul
    def init_consul(self):
        # consul_server
        self.consul_obj = consul.Consul(self.current_ip, port=ConsulAPI.PORT)

    @try_except_consul
    @register_filter
    def register_script(self, name, ip, script):
        # consul_client
        consul_obj = consul.Consul(ip, port=ConsulAPI.PORT)
        check = consul.Check.script(script, self.interval)
        return consul_obj.agent.check.register(name, check=check)

    @try_except_consul
    @register_filter
    def register_http(self, name, ip, url):
        # consul_client
        consul_obj = consul.Consul(ip, port=ConsulAPI.PORT)
        check = consul.Check.http(url,
                                  self.interval,
                                  self.timeout)
        return consul_obj.agent.check.register(name, check=check)

    @try_except_consul
    @register_filter
    def register_tcp(self, name, ip, host, port):
        # consul_client
        consul_obj = consul.Consul(ip, port=ConsulAPI.PORT)
        check = consul.Check.tcp(host,
                                 port,
                                 self.interval,
                                 self.timeout)
        return consul_obj.agent.check.register(name, check=check)

    @try_except_consul
    @register_filter
    def register_ttl(self, name, ip, ttl):
        # consul_client
        consul_obj = consul.Consul(ip, port=ConsulAPI.PORT)
        check = consul.Check.ttl(ttl)
        return consul_obj.agent.check.register(name, check=check)

    @try_except_consul
    def get_check_result(self, state=CHECK_STATES['all']):
        index, results = self.consul_obj.health.state(state)
        return results

    @try_except_consul
    def put_kv(self, key, value):
        return self.consul_obj.kv.put(key, value)

    @try_except_consul
    def delete_kv(self, key):
        self.consul_obj.kv.delete(key)

    @try_except_consul
    def get_kv(self, key):
        index, data = self.consul_obj.kv.get(key)
        if data:
            return data['Value']
        else:
            return False
