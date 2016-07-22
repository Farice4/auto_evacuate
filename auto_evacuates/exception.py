"""
Novaevacuate base exception .
"""

import six
import sys
from log import logger


class NovaEvacuateException(Exception):
    """Base Nova Evacuate Exception
    """
    message = ("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        for k, v in self.kwargs.iteritems():
            if isinstance(v, Exception):
                self.kwargs[k] = six.text_type(v)

        if not message:
            try:
                message = self.message % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                logger.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    logger.error("%s: %s" % (name, value))

                message = self.message
        elif isinstance(message, Exception):
            message = six.text_type(message)

        # NOTE(luisg): We put the actual message in 'msg' so that we can access
        # it, because if we try to access the message via 'message' it will be
        # overshadowed by the class' message attribute
        self.msg = message
        super(NovaEvacuateException, self).__init__(message)

    def __unicode__(self):
        return unicode(self.msg)

    def __str__(self):
        """Encode to utf-8 then wsme api can consume it as well."""
        if not six.PY3:
            return unicode(self.args[0]).encode('utf-8')

        return self.args[0]

    def __unicode__(self):
        """Return a unicode representation of the exception message."""
        return unicode(self.args[0])


class InvalidState(NovaEvacuateException):
    _msg_fmt = ("Invalid resource state.")


class NotAuthorized(NovaEvacuateException):
    _msg_fmt = ("Not authorized.")
    code = 403


class IPMIFailure(NovaEvacuateException):
    _msg_fmt = ("IPMI call failed: %(cmd)s.")


class PowerStateFailure(InvalidState):
    _msg_fmt = ("Failed to set node power state to %(pstate)s.")
