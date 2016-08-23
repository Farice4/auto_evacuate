import logging
import logging.config
import os
import grp
import pwd
from auto_evacuates.config import CONF


class LOGManager(object):
    def __init__(self):
        self.LOG_PATH = CONF.get('log', 'path')
        self.LOG_FILE = CONF.get('log', 'file')
        self.LOG_LEVEL = CONF.get('log', 'default')

    def ensure_log_path(self):
        # ensure LOG_PATH exists
        if not os.path.exists(self.LOG_PATH):
            os.mkdir(self.LOG_PATH)
            uid = pwd.getpwnam("nova").pw_uid
            gid = grp.getgrnam("root").gr_gid
            os.chown(self.LOG_PATH, uid, gid)

    def display_log(self):
        """Log base configure"""
        self.ensure_log_path()
        dictLogConfig = {
            "version": 1,
            "handlers": {
                "fileHandler": {
                    "class": "logging.FileHandler",
                    "formatter": "myFormatter",
                    "filename": "%s" % self.LOG_FILE
                }
            },
            "loggers": {
                "compute": {
                    "handlers": ["fileHandler"],
                    "level": "%s" % self.LOG_LEVEL,
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
logger = logmanager.display_log()
