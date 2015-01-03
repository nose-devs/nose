import os
import unittest
from nose.plugins.plugintest import PluginTester, remove_timings

support = os.path.join(os.path.dirname(__file__), 'support')


class TestExpectedFailure(PluginTester, unittest.TestCase):
    activate = '-v'
    plugins = []
    suitepath = os.path.join(support, 'unexpected_success')

    def test_expected_failure(self):
        print self.output
        output = remove_timings(str(self.output))
        assert output == """\
test (test.TC) ... unexpected success

----------------------------------------------------------------------
Ran 1 test in ...s

FAILED (unexpectedSuccesses=1)
"""
