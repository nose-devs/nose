import os
import unittest
from nose.config import Config

class TestNoseSuite(unittest.TestCase):

    def setUp(self):
        cwd = os.path.dirname(__file__)
        self.support = os.path.abspath(os.path.join(cwd, 'support'))

    def test_module_suite_repr(self):
        from mock import Bucket
        from nose.suite import ModuleSuite

        loader = Bucket()
        conf = Config()
        Bucket.conf = conf
        s = ModuleSuite(loader=loader, modulename='test',
                        filename=os.path.join(self.support, 'test.py'))
        self.assertEqual("%s" % s,
                         "test module test in %s" % self.support)
        s = ModuleSuite(loader=loader, modulename='foo.test_foo',
                        filename=os.path.join(self.support, 'foo',
                                              'test_foo.py'))
        print s
        self.assertEqual("%s" % s,
                         "test module foo.test_foo in %s" % self.support)
        s = ModuleSuite(loader=loader, modulename='foo',
                        filename=os.path.join(self.support, 'foo'))
        print s
        self.assertEqual("%s" % s,
                         "test module foo in %s" % self.support)
        
        
        
if __name__ == '__main__':
    unittest.main()
