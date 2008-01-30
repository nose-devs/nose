import logging
import unittest
from traceback import format_tb

log = logging.getLogger(__name__)


__all__ = ['Failure']


# FIXME probably not the best name, since it is mainly used for errors
class Failure(unittest.TestCase):
    __test__ = False # do not collect
    def __init__(self, exc_class, exc_val, tb=None):
        log.debug("A failure! %s %s %s", exc_class, exc_val, format_tb(tb))
        self.exc_class = exc_class
        self.exc_val = exc_val
        self.tb = tb
        unittest.TestCase.__init__(self)

    def __str__(self):
        return "Failure: %s (%s)" % (
            getattr(self.exc_class, '__name__', self.exc_class), self.exc_val)

    def runTest(self):
        if self.tb is not None:            
            raise self.exc_class, self.exc_val, self.tb
        else:
            raise self.exc_class(self.exc_val)
