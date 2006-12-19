import copy
import os
import sys
import unittest
import nose
from nose.config import Config
from nose.result import TextTestResult
from helpers import iter_compat

class TestNoseCollector(unittest.TestCase):

    def setUp(self):
        self.p = sys.path[:]
       
    def tearDown(self):
        sys.path = self.p[:]
        
    def test_basic_collection(self):
        # self.cfg.verbosity = 7
        c = Config()
        c.where = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               'support'))
        tc = nose.TestCollector(c)
        expect = [ 'test module foo in %s' % c.where,
                   'test module test in %s/test-dir' % c.where,
                   'test module test in %s' % c.where ]
        found = []

        for test in iter_compat(tc):
            found.append(str(test))
        self.assertEqual(found, expect)

    def test_deep_collection(self):
        # self.cfg.verbosity = 4
        c = Config()
        c.where = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               'support'))
        tc = nose.TestCollector(c)

        buf = []
        class dummy:
            pass
        stream = dummy()
        stream.writeln = lambda v='':buf.append(v + '\n')
        rr = TextTestResult(stream, [], 1, c)

        expect = [ 'test module foo in %s' % c.where,
                   'test directory %s/foo in foo' % c.where,
                   'test module foo.bar in %s' % c.where,
                   'test module foo.test_foo in %s' % c.where,
                   'test module dir_test_file in %s/foo/tests' % c.where,
                   'test module test in %s/test-dir' % c.where,
                   'test module test in %s' % c.where,
                   "test class <class 'test.Something'>",
                   'test_something (test.Something)',
                   'test class test.TestTwo',
                   'test.TestTwo.test_whatever' ]
        found = []

        for test in iter_compat(tc):
            print test
            found.append(str(test))
            test.setUp()            
            for t in iter_compat(test):
                print ' ', t
                #test(rr)
                found.append(str(t))
                try:
                    for tt in iter_compat(t):
                        print '   ', tt
                        found.append(str(tt))
                except AttributeError:
                    pass
        self.assertEqual(found, expect)
        
if __name__ == '__main__':
    #import logging
    #logging.basicConfig()
    #logging.getLogger('').setLevel(0)
    unittest.main()
