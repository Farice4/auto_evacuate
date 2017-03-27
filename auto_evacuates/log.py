import logging
import logging.config
import os
import grp
import pwd
from auto_evacuates.config import CONF


class LOGManager(object):
    def __init__(self):
        self.log_path = CONF.get('log', 'path')
        self.log_file = CONF.get('log', 'file')
        self.log_level = CONF.get('log', 'default')
        # mailhost = (host, port)
        exec('self.mailhost = %s' % CONF.get('log', 'mailhost'))
        self.fromaddr = CONF.get('log', 'fromaddr')
        # toaddrs = [addr1, addr2]
        exec('self.toaddrs = %s' % CONF.get('log', 'toaddrs'))
        self.user = CONF.get('log', 'user')
        self.passwd = CONF.get('log', 'passwd')

    def _set_log_path(self):
        # ensure LOG_PATH exists
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)
            uid = pwd.getpwnam("nova").pw_uid
            gid = grp.getgrnam("root").gr_gid
            os.chown(self.log_path, uid, gid)

    def set_log_conf(self):
        """Log base configure"""
        self._set_log_path()
        dictLogConfig = {
            "version": 1,
            "handlers": {
                "fileHandler": {
                    "class": "logging.FileHandler",
                    "formatter": "myFormatter",
                    "filename": "%s" % self.log_file
                },
                "SMTPHandler": {
                    "class": "logging.handlers.SMTPHandler",
                    "level": "WARNING",
                    "formatter": "myFormatter",
                    "mailhost": self.mailhost,
                    "fromaddr": self.fromaddr,
                    "toaddrs": self.toaddrs,
                    "subject": "eayunstack-auto-evacuate",
                    "credentials": (self.user, self.passwd),
                }
            },
            "loggers": {
                "compute": {
                    "handlers": ["fileHandler", "SMTPHandler"],
                    "level": "%s" % self.log_level,
                }
            },

            "formatters": {
                "myFormatter": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s -"
                              "%(message)s"
                }
            }
        }

        logging.config.dictConfig(dictLogConfig)

        logger = logging.getLogger("compute")

        return logger

logmanager = LOGManager()
logger = logmanager.set_log_conf()
