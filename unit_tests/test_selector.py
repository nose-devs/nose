import logging
import os
import re
import unittest
import nose.selector
from nose.config import Config
from nose.selector import log, Selector, test_addr
from nose.util import absdir
from mock import Mod

class TestSelector(unittest.TestCase):

    def tearDown(self):
        logging.getLogger('nose.selector').setLevel(logging.WARN)
    
    def test_exclude(self):
        s = Selector(Config())
        c = Config()
        c.exclude = [re.compile(r'me')]
        s2 = Selector(c)
        
        assert s.matches('test_foo')
        assert s2.matches('test_foo')
        assert s.matches('test_me')
        assert not s2.matches('test_me')
        
    def test_include(self):
        s = Selector(Config())
        c = Config()
        c.include = [re.compile(r'me')]
        s2 = Selector(c)

        assert s.matches('test')
        assert s2.matches('test')
        assert not s.matches('meatball')
        assert s2.matches('meatball')
        assert not s.matches('toyota')
        assert not s2.matches('toyota')
        
        c.include.append(re.compile('toy'))
        assert s.matches('test')
        assert s2.matches('test')
        assert not s.matches('meatball')
        assert s2.matches('meatball')
        assert not s.matches('toyota')
        assert s2.matches('toyota')
        
    def test_want_class(self):
        class Foo:
            pass
        class Bar(unittest.TestCase):
            pass
        class TestMe:
            pass
        
        s = Selector(Config())
        assert not s.wantClass(Foo)
        assert s.wantClass(Bar)
        assert s.wantClass(TestMe)

        tests = test_addr([ ':Bar' ])
        assert s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert not s.wantClass(TestMe, tests)

        tests = test_addr([ ':Bar.baz' ])
        assert s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert not s.wantClass(TestMe, tests)

        tests = test_addr([ ':Blah' ])
        assert not s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert not s.wantClass(TestMe, tests)

        tests = test_addr([ ':Blah.baz' ])
        assert not s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert not s.wantClass(TestMe, tests)

        tests = test_addr([ __name__ ])
        assert s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert s.wantClass(TestMe, tests)

        tests = test_addr([ __file__ ])
        assert s.wantClass(Bar, tests)
        assert not s.wantClass(Foo, tests)
        assert s.wantClass(TestMe, tests)
        
    def test_want_directory(self):
        s = Selector(Config())
        assert s.wantDirectory('test')
        assert not s.wantDirectory('test/whatever')
        assert s.wantDirectory('whatever/test')
        assert not s.wantDirectory('/some/path/to/unit_tests/support')

        # default src directory
        assert s.wantDirectory('lib')
        assert s.wantDirectory('src')
        
        # this looks on disk for support/foo, which is a package
        here = os.path.abspath(os.path.dirname(__file__))
        support = os.path.join(here, 'support')
        tp = os.path.normpath(os.path.join(support, 'foo'))
        assert s.wantDirectory(tp)
        # this looks for support, which is not a package
        assert not s.wantDirectory(support)        
        
    def test_want_file(self):

        #logging.getLogger('nose.selector').setLevel(logging.DEBUG)
        #logging.basicConfig()
        
        c = Config()
        c.where = [absdir(os.path.join(os.path.dirname(__file__), 'support'))]
        base = c.where[0]
        s = Selector(c)

        assert not s.wantFile('setup.py')
        assert not s.wantFile('/some/path/to/setup.py')
        assert not s.wantFile('ez_setup.py')
        assert not s.wantFile('.test.py')
        assert not s.wantFile('_test.py')
        assert not s.wantFile('setup_something.py')
        
        assert s.wantFile('test.py')
        assert s.wantFile('foo/test_foo.py')
        assert s.wantFile('bar/baz/test.py', package='baz')
        assert not s.wantFile('foo.py', package='bar.baz')
        assert not s.wantFile('test_data.txt')
        assert not s.wantFile('data.text', package='bar.bz')
        assert not s.wantFile('bar/baz/__init__.py', package='baz')

        tests = test_addr([ 'test.py', 'other/file.txt' ], base)
        assert s.wantFile(os.path.join(base, 'test.py'), tests=tests)
        assert not s.wantFile(os.path.join(base,'foo/test_foo.py'),
                              tests=tests)
        assert not s.wantFile(os.path.join(base,'bar/baz/test.py'),
                              package='baz', tests=tests)
        # still not a python module... some plugin might want it,
        # but the default selector doesn't
        assert not s.wantFile(os.path.join(base,'other/file.txt'),
                              tests=tests)

        tests = test_addr([ 'a.module' ], base)
        assert not s.wantFile(os.path.join(base, 'test.py'),
                              tests=tests)
        assert not s.wantFile(os.path.join(base, 'foo/test_foo.py'),
                              tests=tests)
        assert not s.wantFile(os.path.join(base, 'test-dir/test.py'),
                              package='baz', tests=tests)
        assert not s.wantFile(os.path.join(base, 'other/file.txt'),
                              tests=tests)
        assert s.wantFile('/path/to/a/module.py', tests=tests)
        assert s.wantFile('/another/path/to/a/module/file.py', tests=tests)
        assert not s.wantFile('/path/to/a/module/data/file.txt', tests=tests)
        
    def test_want_function(self):
        def foo():
            pass
        def test_foo():
            pass
        def test_bar():
            pass
        
        s = Selector(Config())
        assert s.wantFunction(test_bar)
        assert s.wantFunction(test_foo)
        assert not s.wantFunction(foo)

        tests = test_addr([ ':test_bar' ])
        assert s.wantFunction(test_bar, tests)
        assert not s.wantFunction(test_foo, tests)
        assert not s.wantFunction(foo, tests)

        tests = test_addr([ __file__ ])
        assert s.wantFunction(test_bar, tests)
        assert s.wantFunction(test_foo, tests)
        assert not s.wantFunction(foo, tests)

    def test_want_method(self):
        class Baz:
            def test_me(self):
                pass
            def test_too(self):
                pass
            def other(self):
                pass
            
        s = Selector(Config())
        
        assert s.wantMethod(Baz.test_me)
        assert s.wantMethod(Baz.test_too)
        assert not s.wantMethod(Baz.other)

        tests = test_addr([ ':Baz.test_too' ])
        assert s.wantMethod(Baz.test_too, tests)
        assert not s.wantMethod(Baz.test_me, tests)                
        assert not s.wantMethod(Baz.other, tests)

        tests = test_addr([ ':Baz' ])
        assert s.wantMethod(Baz.test_too, tests)
        assert s.wantMethod(Baz.test_me, tests)
        assert not s.wantMethod(Baz.other, tests)

        tests = test_addr([ ':Spaz' ])
        assert not s.wantMethod(Baz.test_too, tests)
        assert not s.wantMethod(Baz.test_me, tests)
        assert not s.wantMethod(Baz.other, tests)
        
    def test_want_module(self):
        m = Mod('whatever')
        m2 = Mod('this.that')
        m3 = Mod('this.that.another')
        m4 = Mod('this.that.another.one')
        m5 = Mod('test.something')
        m6 = Mod('a.test')
        m7 = Mod('my_tests')
        m8 = Mod('__main__')
        
        s = Selector(Config())
        assert not s.wantModule(m)
        assert not s.wantModule(m2)
        assert not s.wantModule(m3)
        assert not s.wantModule(m4)
        assert not s.wantModule(m5)
        assert s.wantModule(m6)
        assert s.wantModule(m7)
        assert not s.wantModule(m8)
        
        tests = test_addr([ 'this.that.another' ])
        assert not s.wantModule(m, tests)
        assert s.wantModule(m2, tests)
        assert s.wantModule(m3, tests)
        assert s.wantModule(m4, tests)        
        assert not s.wantModule(m5, tests)
        assert not s.wantModule(m6, tests)
        assert not s.wantModule(m7, tests)
        assert not s.wantModule(m8, tests)
        
    def test_want_module_tests(self):
        m = Mod('whatever')
        m2 = Mod('this.that')
        m3 = Mod('this.that.another')
        m4 = Mod('this.that.another.one')
        m5 = Mod('test.something')
        m6 = Mod('a.test')
        m7 = Mod('my_tests')
        m8 = Mod('__main__')
        
        s = Selector(Config())
        assert not s.wantModuleTests(m)
        assert not s.wantModuleTests(m2)
        assert not s.wantModuleTests(m3)
        assert not s.wantModuleTests(m4)
        assert not s.wantModuleTests(m5)
        assert s.wantModuleTests(m6)
        assert s.wantModuleTests(m7)
        assert s.wantModuleTests(m8)
        
        tests = test_addr([ 'this.that.another' ])
        assert not s.wantModuleTests(m, tests)
        assert not s.wantModuleTests(m2, tests)
        assert s.wantModuleTests(m3, tests)
        assert s.wantModuleTests(m4, tests)        
        assert not s.wantModuleTests(m5, tests)
        assert not s.wantModuleTests(m6, tests)
        assert not s.wantModuleTests(m7, tests)
        assert not s.wantModuleTests(m8, tests)

    def test_module_in_tests(self):
        s = Selector(Config())
        # s.tests = [ 'ever', 'what', 'what.ever' ]

        w = Mod('what')
        we = Mod('whatever')
        w_e = Mod('what.ever')
        w_n = Mod('what.not')
        f_e = Mod('for.ever')

        tests = test_addr([ 'what' ])
        assert s.moduleInTests(w, tests)
        assert s.moduleInTests(w, tests, True)
        assert s.moduleInTests(w_e, tests)
        assert s.moduleInTests(w_e, tests, True)
        assert s.moduleInTests(w_n, tests)
        assert s.moduleInTests(w_n, tests, True)
        assert not s.moduleInTests(we, tests)
        assert not s.moduleInTests(we, tests, True)
        assert not s.moduleInTests(f_e, tests)
        assert not s.moduleInTests(f_e, tests, True)

        tests = test_addr([ 'what.ever' ])
        assert not s.moduleInTests(w, tests)
        assert s.moduleInTests(w, tests, True)
        assert s.moduleInTests(w_e, tests)
        assert s.moduleInTests(w_e, tests, True)
        assert not s.moduleInTests(w_n, tests)
        assert not s.moduleInTests(w_n, tests, True)
        assert not s.moduleInTests(we, tests)
        assert not s.moduleInTests(we, tests, True)
        assert not s.moduleInTests(f_e, tests)
        assert not s.moduleInTests(f_e, tests, True)

        tests = test_addr([ 'what.ever', 'what.not' ])
        assert not s.moduleInTests(w, tests)
        assert s.moduleInTests(w, tests, True)
        assert s.moduleInTests(w_e, tests)
        assert s.moduleInTests(w_e, tests, True)
        assert s.moduleInTests(w_n, tests)
        assert s.moduleInTests(w_n, tests, True)
        assert not s.moduleInTests(we, tests)
        assert not s.moduleInTests(we, tests, True)
        assert not s.moduleInTests(f_e, tests)
        assert not s.moduleInTests(f_e, tests, True)

    def test_module_in_tests_file(self):
        base = absdir(os.path.join(os.path.dirname(__file__), 'support'))
        c = Config()
        c.where = [base]
        s = Selector(c)

        f = Mod('foo', file=base+'/foo/__init__.pyc')
        t = Mod('test', path=base)
        f_t_f = Mod('foo.test_foo', path=base)
        d_t_t = Mod('test', path=base+'/test-dir')
        
        tests = test_addr([ 'test.py' ], base)
        assert not s.moduleInTests(f, tests)
        assert s.moduleInTests(t, tests)
        assert not s.moduleInTests(f_t_f, tests)
        assert not s.moduleInTests(d_t_t, tests)
        
        tests = test_addr([ 'foo/' ], base)
        assert s.moduleInTests(f, tests)
        assert s.moduleInTests(f_t_f, tests)
        assert not s.moduleInTests(t, tests)
        assert not s.moduleInTests(d_t_t, tests)

        tests = test_addr([ 'foo/test_foo.py' ], base)
        assert not s.moduleInTests(f, tests)
        assert s.moduleInTests(f_t_f, tests)
        assert not s.moduleInTests(t, tests)
        assert not s.moduleInTests(d_t_t, tests)
        
        tests = test_addr([ 'test-dir/test.py' ], base)
        assert not s.moduleInTests(f, tests)
        assert not s.moduleInTests(t, tests)
        assert not s.moduleInTests(f_t_f, tests)
        assert s.moduleInTests(d_t_t, tests)


        
if __name__ == '__main__':
    # log.setLevel(logging.DEBUG)
    unittest.main()
