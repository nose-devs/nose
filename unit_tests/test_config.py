import re
import unittest
import nose.config
from nose.core import configure

class TestNoseConfig(unittest.TestCase):

    def test_defaults(self):
        c = nose.config.Config()
        assert c.addPaths == True
        assert c.capture == True
        assert c.detailedErrors == False
        # FIXME etc
        
    def test_reset(self):
        c = nose.config.Config()
        c.include = 'include'        
        assert c.include == 'include'
        c.reset()
        assert c.include is None

    def test_update(self):
        c = nose.config.Config()
        c.update({'exclude':'x'})
        assert c.exclude == 'x'

    def test_multiple_include(self):
        c = nose.config.Config()
        c.configure(['--include=a', '--include=b'])
        self.assertEqual(c.include, [re.compile('a'), re.compile('b')])

    def test_single_include(self):
        c = nose.config.Config()
        c.configure(['--include=b'])
        self.assertEqual(c.include, [re.compile('b')])

    def test_plugins(self):
        c = nose.config.Config()
        assert c.plugins
        c.plugins.begin()

if __name__ == '__main__':
    unittest.main()
