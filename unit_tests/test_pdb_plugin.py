import sys
import unittest
from nose.plugins import debug

class StubPdb:
    called = False
    def post_mortem(self, tb):
        self.called = True

class TestPdbPlugin(unittest.TestCase):

    def setUp(self):
        self._pdb = debug.pdb
        debug.pdb = StubPdb()

    def tearDown(self):
        debug.pdb = self._pdb

    def test_plugin_api(self):
        p = debug.Pdb()
        p.addOptions
        p.configure
        p.addError
        p.addFailure

    def test_plugin_calls_pdb(self):
        p = debug.Pdb()

        try:
            raise Exception("oops")
        except:
            err = sys.exc_info()
    
        p.enabled = True
        p.enabled_for_failures = True

        p.addError(None, err)
        assert debug.pdb.called


if __name__ == '__main__':
    unittest.main()
