import os
import tempfile
import unittest

from nose.plugins import PluginTester
from nose.plugins.testid import TestId


support = os.path.join(os.path.dirname(__file__), 'support')
idfile = tempfile.mktemp()

def teardown():
     try:
         os.remove(idfile)
     except OSError:
         pass

class TestVerbose(PluginTester, unittest.TestCase):
    activate = '--with-id'
    plugins = [TestId()]
    args = ['-v', '--id-file=%s' % idfile]
    suitepath = os.path.join(support, 'idp')

    def test_ids_added_to_output(self):
        print '#' * 70
        print str(self.output)
        print '#' * 70

        for line in self.output:
            if line.startswith('='):
                break
            if not line.strip():
                continue
            if 'test_gen' in line and not '(0,)' in line:
                assert not line.startswith('#'), \
                       "Generated test line '%s' should not have id" % line
            else:
                assert line.startswith('#'), \
                       "Test line '%s' missing id" % line.strip()
            

    # test that id file is written

    # test that id numbers are intercepted and translated in
    # loadTestsFromNames hook

    # test that if loadTestsFromNames finds names, id file is not re-written
        
        
if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        teardown()
    
