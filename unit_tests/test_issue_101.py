import sys
import unittest
from nose.plugins.errorclass import ErrorClass, ErrorClassPlugin

class TestErrorClassWithStringException(unittest.TestCase):

    def test_string_exception_not_masked(self):

        class X(Exception):
            pass

        class EP(ErrorClassPlugin):
            xes = ErrorClass(X, label='XXX', isfailure=True)

        try:
            raise "oh no!"
        except:
            exc = sys.exc_info()
        
        ep = EP()
        self.assertEqual(ep.addError(None, exc), None)
