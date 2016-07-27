from auto_evacuates.app import manage
from auto_evacuates.novacheck.network.network import Net_Interface
from auto_evacuates.log import logger
import time
import os


def main():
    """use main function load manage.manager functiong,
    the program until background running

    """
    led = Net_Interface()
    pid = os.fork()
    if pid == 0:
        os.setsid()
        while True:
            try:
                if led.leader():
                    manage.manager()
                else:
                    logger.info("node is not leader,do not any check")
            except Exception as e:
                logger.error("auto nova evacuate error: %s" % e)
            time.sleep(30)
    else:
        os._exit(0)

if __name__ == "__main__":
    main()
