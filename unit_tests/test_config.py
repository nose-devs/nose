import re
import os
import tempfile
import unittest
import nose.config
import warnings



class TestNoseConfig(unittest.TestCase):

    def test_defaults(self):
        c = nose.config.Config()
        assert c.addPaths == True
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

    def test_testnames(self):
        c = nose.config.Config()
        c.configure(['program', 'foo', 'bar', 'baz.buz.biz'])
        self.assertEqual(c.testNames, ['foo', 'bar', 'baz.buz.biz'])

    def test_where(self):
        # we don't need to see our own warnings
        warnings.filterwarnings(action='ignore',
                                category=DeprecationWarning,
                                module='nose.config')

        here = os.path.dirname(__file__)
        support = os.path.join(here, 'support')
        foo = os.path.abspath(os.path.join(support, 'foo'))
        c = nose.config.Config()
        c.configure(['program', '-w', foo, '-w', 'bar'])
        self.assertEqual(c.workingDir, foo)
        self.assertEqual(c.testNames, ['bar'])

if __name__ == '__main__':
    unittest.main()
