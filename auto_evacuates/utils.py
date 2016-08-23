"""auto evacuate public module"""

import os
import paramiko
import socket
from auto_evacuates.exception import NovaClientError, IPMIError
from novaclient import exceptions


def ssh_connect(ipaddr, command, key_file=os.environ['HOME']
                + '/.ssh/id_rsa_ipmi', ssh_port=22, username='root',
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
        raise IPMIError('AuthenticationFailure:%s' % error_info)
    except socket.timeout:
        error_info = ('Can not connect to %s, Connect time out!'
                      % ipaddr)
        raise IPMIError('ConnectionTimeout:%s' % error_info)
    except socket.error:
        error_info = ('Can not connect to %s, Connect Destination Host'
                      'Unreachable !' % ipaddr)
        raise IPMIError('ConnectionError:%s' % error_info)
    finally:
        s.close()
    return ret, result_out, result_err


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
