class BaseException(Exception):

    name = "NovaEvacuateException"

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        formatted_string = "%s:%s" % (self.name, self.message)
        return formatted_string


class NovaClientError(BaseException):

    pass


class SSHError(BaseException):

    pass


class ConsulError(BaseException):

    pass
