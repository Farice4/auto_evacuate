# log_with_config.py
import logging
import logging.config


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
                "filename": "/var/log/nova/auto-evacute.log"
            }
        },
        "loggers": {
            "compute": {
                "handlers": ["fileHandler"],
                "level": "INFO",
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
