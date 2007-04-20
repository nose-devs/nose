import os
import tempfile
import unittest

from nose.plugins import PluginTester
from nose.plugins.testid import TestId
from cPickle import dump, load

support = os.path.join(os.path.dirname(__file__), 'support')
idfile = tempfile.mktemp()

def teardown():
     try:
         os.remove(idfile)
     except OSError:
         pass

class TestDiscoveryMode(PluginTester, unittest.TestCase):
    activate = '--with-id'
    plugins = [TestId()]
    args = ['-v', '--id-file=%s' % idfile]
    suitepath = os.path.join(support, 'idp')

    def test_ids_added_to_output(self):
        print '>' * 70
        print str(self.output)
        print '<' * 70

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
    def test_id_file_contains_ids_seen(self):
        assert os.path.exists(idfile)
        fh = open(idfile, 'r')
        ids = load(fh)
        fh.close()
        assert ids
        assert ids.keys()
        self.assertEqual(map(int, ids.keys()), ids.keys())
        assert ids.values()


class TestLoadNamesMode(PluginTester, unittest.TestCase):
    """NOTE that this test passing requires the previous test case to
    be run! (Otherwise the ids file will not exist)
    """
    activate = '--with-id'
    plugins = [TestId()]
    args = ['-v', '--id-file=%s' % idfile, '#2', '#5']
    suitepath = None

    def makeSuite(self):
        return None

    def test_load_ids(self):
        print '#' * 70
        print str(self.output)
        print '#' * 70

        for line in self.output:
            if line.startswith('#'):
                assert line.startswith('#2 ') or line.startswith('#5 '), \
                       "Unexpected test line '%s'" % line
        assert os.path.exists(idfile)
        fh = open(idfile, 'r')
        ids = load(fh)
        fh.close()
        assert ids
        assert ids.keys()
        self.assertEqual(filter(lambda i: int(i), ids.keys()), ids.keys())
        assert len(ids.keys()) > 2
    
    # test that id numbers are intercepted and translated in
    # loadTestsFromNames hook
    # test that if loadTestsFromNames finds names, id file is not re-written

class TestLoadNamesMode_2(PluginTester, unittest.TestCase):
    """NOTE that this test passing requires the previous test case to
    be run! (Otherwise the ids file will not exist)

    Tests that generators still only have id on one line
    """
    activate = '--with-id'
    plugins = [TestId()]
    args = ['-v', '--id-file=%s' % idfile, '#9']
    suitepath = None

    def makeSuite(self):
        return None

    def test_load_ids(self):
        print '%' * 70
        print str(self.output)
        print '%' * 70

        count = 0
        for line in self.output:
            if line.startswith('#'):
                count += 1
        self.assertEqual(count, 1)

    # Test with doctests
    
if __name__ == '__main__':
    import logging
    logging.basicConfig()
    l = logging.getLogger('nose.plugins.testid')
    l.setLevel(logging.DEBUG)
    
    try:
        unittest.main()
    finally:
        teardown()
    
