import os
import sys
import unittest
from nose import SkipTest
from nose.plugins.plugintest import PluginTester, remove_timings

support = os.path.join(os.path.dirname(__file__), 'support')

class TestUnexpectedSuccess(PluginTester, unittest.TestCase):
    activate = '-v'
    plugins = []
    suitepath = os.path.join(support, 'unexpected_success')

    def setUp(self):
        super(TestUnexpectedSuccess, self).setUp()
        if sys.version_info < (2, 7):
            raise SkipTest('unexpected success not available in python<2.7')

    def test_unexpected_success(self):
        print self.output
        output = remove_timings(str(self.output))
        assert output == """\
test (test.TC) ... unexpected success

----------------------------------------------------------------------
Ran 1 test in ...s

FAILED (unexpectedSuccesses=1)
"""
