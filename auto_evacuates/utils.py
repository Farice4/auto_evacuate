"""auto evacuate public module"""

import os
import paramiko
import socket
import consul
from auto_evacuates.exception import SSHError, NovaClientError, ConsulError
from novaclient import exceptions


def ssh_connect(ipaddr, command, key_file=os.environ['HOME']
                + '/.ssh/id_rsa', ssh_port=22, username='root',
                timeout=3):
    """paramiko ssh client connect

    :return execute command result
    """
    key = paramiko.RSAKey.from_private_key_file(key_file)
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ret = False

    try:
        s.connect(ipaddr, ssh_port, username=username,
                  pkey=key, timeout=timeout)
        stdin, stdout, stderr = s.exec_command(command)
        result_out = stdout.read()
        result_err = stderr.read()
        ret = True
    except paramiko.ssh_exception.AuthenticationException:
        error_info = ('Can not connect to %s, Authentication (publickey)'
                      'failed !' % ipaddr)
        raise SSHError('AuthenticationFailure:%s' % error_info)
    except socket.timeout:
        error_info = ('Can not connect to %s, Connect time out!'
                      % ipaddr)
        raise SSHError('ConnectionTimeout:%s' % error_info)
    except socket.error:
        error_info = ('Can not connect to %s, Connect Destination Host'
                      'Unreachable !' % ipaddr)
        raise SSHError('ConnectionError:%s' % error_info)
    finally:
        s.close()
    return ret, result_out, result_err


def try_except_consul(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except consul.ACLDisabled as e:
            error_info = "ACLDisabled: %s" % e
            raise ConsulError(error_info)
        except consul.ACLPermissionDenied as e:
            error_info = "ACLPermissionDenied: %s" % e
            raise ConsulError(error_info)
        except consul.ConsulException as e:
            error_info = "ConsulException: %s" % e
            raise ConsulError(error_info)
        except consul.NotFound as e:
            error_info = "NotFound: %s" % e
            raise ConsulError(error_info)
        except consul.Timeout as e:
            error_info = "Timeout: %s" % e
            raise ConsulError(error_info)
    return wrapper


def try_except_novaclient(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.UnsupportedVersion as e:
            error_info = "UnsupportedVersion: %s" % e
            raise NovaClientError(error_info)
        except exceptions.AuthorizationFailure as e:
            error_info = "AuthorizationFailure: %s " % e
            raise NovaClientError(error_info)
        except exceptions.CommandError as e:
            error_info = "CommandError: %s" % e
            raise NovaClientError(error_info)
        except exceptions.ClientException as e:
            error_info = "ClientException: %s" % e
            raise NovaClientError(error_info)
        except Exception as e:
            error_info = "Exception: %s" % e
            raise NovaClientError(error_info)
    return wrapper


def ele_filter(eles_list):
    '''
    param:eles_list like [[].....]
    return:tmp_list
    '''
    length = len(eles_list)
    tmp_list = eles_list[0][:]
    for i in range(1, length):
        for ele in eles_list[0]:
            if ele not in eles_list[i] and ele in tmp_list:
                tmp_list.remove(ele)
    return tmp_list
