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


#test case for #462
class TestClassFixture(PluginTester, unittest.TestCase):
    activate = '--processes=1'
    plugins = [MultiProcess()]
    suitepath = os.path.join(support, 'class.py')

    def runTest(self):
        assert str(self.output).strip().endswith('OK')
        assert 'Ran 2 tests' in self.output
    def tearDown(self):
        MultiProcess.status.pop('active')

