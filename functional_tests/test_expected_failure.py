import os
import sys
import unittest
from nose import SkipTest
from nose.plugins.plugintest import PluginTester, remove_timings

support = os.path.join(os.path.dirname(__file__), 'support')

class TestExpectedFailure(PluginTester, unittest.TestCase):
    activate = '-v'
    plugins = []
    suitepath = os.path.join(support, 'expected_failure')

    def setUp(self):
        super(TestExpectedFailure, self).setUp()
        if sys.version_info < (2, 7):
            raise SkipTest('expected failure not available in python<2.7')

    def test_expected_failure(self):
        print self.output
        output = remove_timings(str(self.output))
        assert output == """\
test (test.TC) ... expected failure

----------------------------------------------------------------------
Ran 1 test in ...s

OK (expectedFailures=1)
"""
