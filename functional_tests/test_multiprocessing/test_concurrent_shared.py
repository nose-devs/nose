import os
import unittest

from nose.plugins import PluginTester
from nose.plugins.skip import SkipTest
from nose.plugins.multiprocess import MultiProcess


support = os.path.join(os.path.dirname(__file__), 'support')


def setup():
    try:
        import multiprocessing
        if 'active' in MultiProcess.status:
            raise SkipTest("Multiprocess plugin is active. Skipping tests of "
                           "plugin itself.")
    except ImportError:
        raise SkipTest("multiprocessing module not available")


class TestConcurrentShared(PluginTester, unittest.TestCase):
    activate = '--processes=2'
    plugins = [MultiProcess()]
    suitepath = os.path.join(support, 'concurrent_shared')

    def runTest(self):
        assert 'Ran 2 tests in 1.' in self.output, "make sure two tests use 1.x seconds (no more than 2 seconsd)"
        assert str(self.output).strip().endswith('OK')
    def tearDown(self):
        MultiProcess.status.pop('active')

