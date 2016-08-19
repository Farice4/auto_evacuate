import eventlet
eventlet.monkey_patch()
from auto_evacuates.consul_api import is_leader
from auto_evacuates.log import logger
from auto_evacuates.config import CONF
from auto_evacuates.exception import IPMIError
from auto_evacuates.ipmi import IPMIManager
import re
import sys

IPMI_ADDR_FILE = CONF.get('idrac', 'file')


class Manager(object):
    def __init__(self):
        self.ipmi_objs = []
        self.pool = eventlet.GreenPool()  # give a greenthread size?

    def run(self):
        """check cluster status every 30s, if some serious error
        occurred, _handle_xxx_error() will handle them"""
        logger.info("start worker")
        self._init_ipmi(IPMI_ADDR_FILE)
        while True:
            try:
                if is_leader():
                    logger.debug("Start checking IPMI")
                    # TODO: add some comment about error_nodes
                    error_nodes = self._check_ipmi()
                    if error_nodes:
                        self._handle_ipmi_error(error_nodes)

                    logger.debug("Start checking network")
                    error_nodes = self._check_network()
                    if error_nodes:
                        self._handle_network_error(error_nodes)

                    logger.debug("Start checking service")
                    error_nodes = self._check_service()
                    if error_nodes:
                        self._handle_service_error(error_nodes)
                else:
                    logger.info("This node is not the leader,"
                                "no need to do any check")
                # TODO, send email?
            except Exception as e:
                # TODO, catch speical exception, raise unknow excep to caller?
                logger.error("Failed to auto evacuate: %s" % e)
            eventlet.sleep(30)

    def _init_ipmi(self, conf):
        """ ipmi_objs = [
            {
                'hostname':'node-17.eayun.com',
                'shortname':'node-17',
                'macaddr':'xxxx',
                'pxeaddr': 'xxxxx',
                'ipmiaddr':'xxxx',
                'manager':IPMIManager(ipmiaddr)
            },
            {
                // other node
            }
        ]
        """
        try:
            with open(conf) as f:
                for l in f.readlines():
                    p = re.compile(r'(.+):(.+):(.+):(.+):(.+):(.+)')
                    hostname, shortname, pxeaddr, roler, macaddr, ipmiaddr \
                        = p.match(l.strip('\n')).groups()
                    if roler == 'compute':
                        item = {
                            'hostname': hostname,
                            'shortname': shortname,
                            'macaddr': macaddr,
                            'pxeaddr': pxeaddr,
                            'ipmiaddr': ipmiaddr,
                            'manager': IPMIManager(ipmiaddr, hostname)
                        }
                        self.ipmi_objs.append(item)
        except Exception as e:
            logger.error('Failed to init ipmi module from ipmi file: %s', e)
            sys.exit(1)

    def _check_ipmi(self):
        """check ipmi power status"""
        error_nodes = []
        try:
            for i in self.ipmi_objs:
                if not i['manager'].is_power_on():
                    error_nodes.append(i)
        except IPMIError as e:
            logger.error("IPMI Error is: %s" % e)
        except Exception as e:
            logger.error("Unknown Error %s" % e)

    def _handle_ipmi_error(self, error_nodes):
        self.pool.imap(self._handle_ipmi_one, error_nodes)

    def _handle_ipmi_one(self, node):
        pass

    def _check_network(self):
        return []

    def _handle_network_error(self, error_nodes):
        pass

    def _check_service(self):
        return []

    def _handle_service_error(self, service_checks):
        pass
