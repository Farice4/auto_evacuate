# log_with_config.py
import logging
import logging.config
from config import CONF

LOG_FILE = CONF.get('log', 'file')
LOG_LEVEL = CONF.get('log', 'default')


def log():
    """
    Based on http://docs.python.org/howto/logging.html#configuring-logging
    """
    dictLogConfig = {
        "version": 1,
        "handlers": {
            "fileHandler": {
                "class": "logging.FileHandler",
                "formatter": "myFormatter",
                "filename": "%s" % LOG_FILE
            }
        },
        "loggers": {
            "compute": {
                "handlers": ["fileHandler"],
                "level": "%s" % LOG_LEVEL,
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

logger = log()
