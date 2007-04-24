import os
import sys
import unittest
from nose.config import Config
from nose.plugins import doctests
from mock import Bucket

# some plugins have 2.4-only features
compat_24 = sys.version_info >= (2, 4)

class TestDoctestErrorHandling(unittest.TestCase):

    def setUp(self):
        self._path = sys.path[:]
        here = os.path.dirname(__file__)
        testdir = os.path.join(here, 'support', 'doctest')
        sys.path.insert(0, testdir)
        p = doctests.Doctest()
        p.can_configure = True
        p.configure(Bucket(), Config())
        self.p = p
        
    def tearDown(self):
        sys.path = self._path[:]
        
    def test_no_doctests_in_file(self):
        p = self.p
        mod = __import__('no_doctests')
        loaded = [ t for t in p.loadTestsFromModule(mod) ]
        assert not loaded, "Loaded %s from empty module" % loaded

    def test_err_doctests_raises_exception(self):
        p = self.p
        mod = __import__('err_doctests')
        try:
            loaded = [ t for t in p.loadTestsFromModule(mod) ]
        except ValueError:
            pass
        else:
            if compat_24:
                self.fail("Error doctests file did not raise ValueError")
            else:
                self.assert_(loaded,
                             "No value error, nothing loaded from err tests")
if __name__ == '__main__':
    unittest.main()
