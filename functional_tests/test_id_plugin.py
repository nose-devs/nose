import os
import tempfile
import unittest
from nose.core import TestProgram, TextTestRunner
from nose.config import Config
from nose.exc import SkipTest
from nose.plugins.manager import PluginManager
from cStringIO import StringIO

raise SkipTest('Id plugin not yet written')

from nose.plugins.testid import TestId

here = os.path.abspath(os.path.dirname(__file__))
support = os.path.join(here, 'support')

class TestIdPlugin(unittest.TestCase):

    def setUp(self):
        self.plugins = PluginManager(plugins=[TestId()])
    
    def test_adds_id_to_output(self):
        tests = os.path.join(support, 'package1')
        out = StringIO()
        conf = Config(
            exit=False,
            plugins=self.plugins,
            statusFile=tempfile.mktemp())
        runner = TextTestRunner(stream=out)
        TestProgram(config=conf, testRunner=runner,
                    argv=['test_adds_id_to_output',
                          '--with-id',
                          '-v',
                          tests])
        print out.getvalue()
        assert out.getvalue(), "No output from test run"
        for line in out:
            if line.startswith('-'):
                break            
            assert line.startswith('#'), "Test line %s without id" % line
            
        
        
if __name__ == '__main__':
    unittest.main()
