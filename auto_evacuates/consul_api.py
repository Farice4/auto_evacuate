import consul
import socket
import fcntl
import struct
from auto_evacuates.log import logger


def get_ipaddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ipaddr = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(), 0x8915,
        struct.pack('256s', ifname[:15]))[20:24])
    return ipaddr


def is_leader():
    """
    return if this node is consule leader or not
    """
    # TODO: ugly code
    storage_ip = get_ipaddr('br-storage')
    cs = consul.Consul(storage_ip, 8500)
    try:
        if (cs.status.leader() == (storage_ip + ":8300")):
            return True
        else:
            return False
    except Exception as e:
        logger.info("can't get consul leader, the reason is: %s" % e)
