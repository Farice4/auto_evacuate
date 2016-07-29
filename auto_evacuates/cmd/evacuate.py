from auto_evacuates.app.manage import Manager
from auto_evacuates.novacheck.network.network import NetInterface
from auto_evacuates.log import logger
import time
import os


def main():
    """the program until background running,
    the program in leader execuate all check operate,
    if the leader apear error, all check or fence or
    evacuate not Success
    """

    pid = os.fork()
    if pid == 0:
        os.setsid()
        try:
            Manager.run()
        except Exception as e:
            # TODO: restart manager?
            logger.error("Failed to auto evacuate: %s" % e)
    else:
        os._exit(0)

if __name__ == "__main__":
    main()
