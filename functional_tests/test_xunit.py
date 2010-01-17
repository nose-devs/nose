# -*- coding: utf-8 -*-
import os
import unittest
from nose.plugins.xunit import Xunit
from nose.plugins.skip import Skip
from nose.plugins import PluginTester

support = os.path.join(os.path.dirname(__file__), 'support')
xml_results_filename = os.path.join(support, "xunit.xml")

# the plugin is tested better in unit tests.
# this is just here for a sanity check
    
class TestXUnitPlugin(PluginTester, unittest.TestCase):
    activate = '--with-xunit'
    args = ['-v','--xunit-file=%s' % xml_results_filename]
    plugins = [Xunit(), Skip()]
    suitepath = os.path.join(support, 'xunit')
    
    def runTest(self):
        print str(self.output)
        
        assert "ERROR: test_error" in self.output
        assert "FAIL: test_fail" in self.output
        assert "test_skip (test_xunit_as_suite.TestForXunit) ... SKIP: skipit" in self.output
        assert "XML: %s" % xml_results_filename in self.output
        
        f = open(xml_results_filename,'r')
        result = f.read()
        f.close()
        print result
        
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert '<testsuite name="nosetests" tests="6" errors="2" failures="1" skip="1">' in result
        assert '<testcase classname="test_xunit_as_suite.TestForXunit" name="test_error" time="0">' in result
        assert '<error type="exceptions.Exception" message="日本">' in result
        assert '</testcase>' in result
        assert '</testsuite>' in result


class TestIssue279(PluginTester, unittest.TestCase):
    activate = '--with-xunit'
    args = ['-v','--xunit-file=%s' % xml_results_filename]
    plugins = [Xunit(), Skip()]
    suitepath = os.path.join(support, 'issue279')

    def runTest(self):
        print str(self.output)
        f = open(xml_results_filename,'r')
        result = f.read()
        f.close()
        print result
        assert 'tests="1" errors="1" failures="0" skip="0"' in result
        assert "Exception: I would prefer not to" in result
