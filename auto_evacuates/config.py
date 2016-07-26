import ConfigParser

"""Use ConfigParser define all config,other module use
    config module get data
"""

FILE_PATH = '/etc/autoevacuate/evacuate.conf'


class Config(object):
    """ Load config file"""
    def __init__(self, filename):
        self.cf = ConfigParser.ConfigParser()
        self.file_name = filename
        self.read_file = self.read_config()

    def read_config(self):
        """define config file read"""
        self.cf.read(self.file_name)

    def get(self, section, option):
        """define config file data get"""
        return self.cf.get(section, option)

CONF = Config(FILE_PATH)
