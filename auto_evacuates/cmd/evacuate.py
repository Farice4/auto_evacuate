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

    leder = NetInterface()
    pid = os.fork()
    if pid == 0:
        os.setsid()
        while True:
            try:
                if leder.leader():
                    Manager.run()
                    # Use Manager class under run function program running
                else:
                    logger.info("This node is not the leader,"
                                "no need to do any check")
            except Exception as e:
                logger.error("Failed to auto evacuate: %s" % e)
            time.sleep(30)
    else:
        os._exit(0)

if __name__ == "__main__":
    main()
