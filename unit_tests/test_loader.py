import os
import sys
import unittest
from nose import case, loader
from nose.config import Config
from nose.importer import _import

from helpers import iter_compat
from mock import *

class TestNoseTestLoader(unittest.TestCase):

    def setUp(self):
        cwd = os.path.dirname(__file__)
        self.support = os.path.abspath(os.path.join(cwd, 'support'))
    
    def test_load_from_name_dir(self):        
        l = loader.TestLoader()
        name = os.path.join(self.support, 'test-dir')
        expect = [ 'test module test in %s' % name ]
        found = []
        for test in l.loadTestsFromName(name):
            found.append(str(test))
        # print found
        self.assertEqual(found, expect)

    def test_load_from_name_file(self):
        l = loader.TestLoader()
        name = os.path.join(self.support, 'test.py')
        expect = [ 'test module test in %s' % self.support ]
        found = []
        for test in l.loadTestsFromName(name):
            found.append(str(test))
        # print found
        self.assertEqual(found, expect)

    def test_load_from_name_module(self):
        c = Config()
        c.where = self.support
        l = loader.TestLoader(c)
        name = 'test'
        expect = [ 'test module test in %s' % self.support,
                   'test module test in %s/test-dir' % self.support ]
        found = []
        for test in l.loadTestsFromName(name):
            found.append(str(test))

        c.where = os.path.join(self.support, 'test-dir')
        for test in l.loadTestsFromName(name):
            found.append(str(test))
        print found
        self.assertEqual(found, expect)
                
    def test_load_from_names(self):
        c = Config()
        c.where = self.support
        l = loader.TestLoader(c)

        foo = _import('foo', [self.support], c)
        
        expect = [ 'test module test in %s' % self.support,
                   'test module foo.test_foo in %s' % self.support ]
        found = []
        tests = l.loadTestsFromNames(['test', 'foo.test_foo'])
        for t in iter_compat(tests):
            found.append(str(t))
        self.assertEqual(found, expect)
        
        expect = [ 'test module foo in %s' % self.support ]
        tests = l.loadTestsFromNames(None, module=foo)
        found = [ str(tests) ]
        self.assertEqual(found, expect)

    def test_load_from_names_compat(self):
        c = Config()
        l = loader.TestLoader(c)
        
        # implicit : prepended when module specified
        names = ['TestNoseTestLoader.test_load_from_names_compat']
        tests = l.loadTestsFromNames(names, sys.modules[__name__])

        # should be... me
        expect = [ 'test_load_from_names_compat '
                   '(%s.TestNoseTestLoader)' % __name__ ]
        found = []
        # print tests
        for test in iter_compat(tests):
            # print test
            for t in iter_compat(test):
                # print t
                found.append(str(t))
        self.assertEqual(found, expect)
                
        # explict : ok too
        c.tests = []
        found = []
        names[0] = ':' + names[0]
        tests = l.loadTestsFromNames(names, sys.modules[__name__])
        for test in iter_compat(tests):
            for t in iter_compat(test):
                found.append(str(t))
        self.assertEqual(found, expect)
        
    def test_load_from_class(self):
        c = Config()
        class TC:
            test_not = 1
            def test_me(self):
                pass
            def not_a_tes_t(self):
                pass

        class TC2(unittest.TestCase):
            def test_whatever(self):
                pass

        class TC3(TC2):
            def test_somethingelse(self):
                pass
                
        l = loader.TestLoader()
        cases = l.loadTestsFromTestCase(TC)
        # print cases
        assert isinstance(cases[0], case.MethodTestCase)
        assert len(cases) == 1
        self.assertEqual(str(cases[0]), '%s.TC.test_me' % __name__)

        cases2 = l.loadTestsFromTestCase(TC2)
        # print cases2
        assert isinstance(cases2[0], unittest.TestCase)
        assert len(cases2) == 1
        self.assertEqual(str(cases2[0]), 'test_whatever (%s.TC2)' % __name__)

        cases3 = l.loadTestsFromTestCase(TC3)
        # print cases3
        assert len(cases3) == 2
        self.assertEqual(str(cases3[0]),
                         'test_somethingelse (%s.TC3)' % __name__)
        self.assertEqual(str(cases3[1]),
                         'test_whatever (%s.TC3)' % __name__)

    def test_load_generator_method(self):
        class TC(object):
            _setup = False
            
            def setUp(self):
                assert not self._setup                    
                self._setup = True
            
            def test_generator(self):
                for a in range(0,5):
                    yield self.check, a

            def check(self, val):
                assert self._setup       
                assert val >= 0
                assert val <= 5

        l = loader.TestLoader()
        cases = l.loadTestsFromTestCase(TC)
        count = 0
        for suite in iter_compat(cases):
            for case in iter_compat(suite):
                assert str(case) == '%s.TC.test_generator:(%d,)' % \
                    (__name__, count)
                count += 1
        assert count == 5

    def test_load_generator_func(self):
        m = Mod('testo', __path__=None)

        def testfunc(i):
            pass
        
        def testgenf():
            for i in range(0, 5):
                yield testfunc, i

        m.testgenf = testgenf
        
        l = loader.TestLoader()
        cases = l.loadTestsFromModule(m)
        print cases
        count = 0
        for case in iter_compat(cases):
            # print case
            self.assertEqual(str(case),
                             '%s.testgenf:(%d,)' % (__name__, count))
            count += 1
        assert count == 5

    def test_get_module_funcs(self):
        from StringIO import StringIO
        
        m = Mod('testo', __path__=None)

        def test_func():
            pass

        class NotTestFunc(object):
            def __call__(self):
                pass

        class Selector:
            classes = []
            funcs = []
            
            def wantClass(self, test):
                self.classes.append(test)
                return False
            
            def wantFunction(self, test):
                self.funcs.append(test)
                return True            
        sel = Selector()
        
        m.test_func = test_func
        m.test_func_not_really = NotTestFunc()
        m.StringIO = StringIO
        m.buffer = StringIO()
        
        l = loader.TestLoader(selector=sel)
        tests = l.testsInModule(m)
        
        print tests
        print sel.funcs
        assert test_func in sel.funcs
        assert not m.test_func_not_really in sel.funcs
        assert len(sel.funcs) == 1

    def test_pkg_layout_lib_tests(self):
        from mock import Result
        from nose.util import absdir
        r = Result()
        l = loader.TestLoader()
        where = absdir(os.path.join(os.path.dirname(__file__),
                                    'support/pkgorg'))
        print "where", where
        print "/lib on path before load?", where + '/lib' in sys.path
        tests = l.loadTestsFromDir(where)
        print "/lib on path after load?", where + '/lib' in sys.path
        print "tests", tests
        for t in tests:
            print "test", t
            # this will raise an importerror if /lib isn't on the path
            t(r)
        assert where + '/lib' in sys.path
        
if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('').setLevel(0)
    #logging.getLogger('nose.importer').setLevel(0)
    unittest.main() #testLoader=loader.TestLoader())
