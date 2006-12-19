import os
import re
import unittest
import nose.selector
from nose.config import Config
from nose.selector import log, Selector
from nose.util import absdir
from mock import Mod

class TestSelector(unittest.TestCase):

    def test_anytest(self):

        def exact_file_a(filename, modname, funcname):
            if filename is None:
                return None
            return filename == '/a/file.py'
        
        def exact_file_b(filename, modname, funcname):
            if filename is None:
                return None
            return filename == '/a/nother/file.py'

        def exact_module_a(filename, modname, funcname):
            if modname is None:
                return None
            return modname == 'some.module'

        def exact_module_b(filename, modname, funcname):
            if modname is None:
                return None
            return modname == 'some.other.module'

        c = Config()
        s = Selector(c)
        s.tests = [ '/a/file.py', 'some.module' ]

        # in these cases, there is a test that doesn't care
        # so they all pass
        assert s.anytest(exact_file_a)
        assert s.anytest(exact_file_b)        
        assert s.anytest(exact_module_a)
        assert s.anytest(exact_module_b)

        # no test matches file b
        s.tests = [ '/a/file.py' ]
        assert s.anytest(exact_file_a)
        assert not s.anytest(exact_file_b)        
        assert s.anytest(exact_module_a)
        assert s.anytest(exact_module_b)

        s.tests = [ '/a/file.py', '/that/file.py' ]
        assert s.anytest(exact_file_a)
        assert not s.anytest(exact_file_b)        
        assert s.anytest(exact_module_a)
        assert s.anytest(exact_module_b)
        
        # no test matches module b
        s.tests = [ 'some.module' ]
        assert s.anytest(exact_file_a)
        assert s.anytest(exact_file_b)        
        assert s.anytest(exact_module_a)
        assert not s.anytest(exact_module_b)

        # no test matches module b
        s.tests = [ 'some.module', 'blah.blah' ]
        assert s.anytest(exact_file_a)
        assert s.anytest(exact_file_b)        
        assert s.anytest(exact_module_a)
        assert not s.anytest(exact_module_b)
        
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

        s.tests = [ ':Bar' ]
        assert s.wantClass(Bar)
        assert not s.wantClass(Foo)
        assert not s.wantClass(TestMe)

        s.tests = [ ':Bar.baz' ]
        assert s.wantClass(Bar)
        assert not s.wantClass(Foo)
        assert not s.wantClass(TestMe)

        s.tests = [ ':Blah' ]
        assert not s.wantClass(Bar)
        assert not s.wantClass(Foo)
        assert not s.wantClass(TestMe)

        s.tests = [ ':Blah.baz' ]
        assert not s.wantClass(Bar)
        assert not s.wantClass(Foo)
        assert not s.wantClass(TestMe)

        s.tests = [ __name__ ]
        assert s.wantClass(Bar) == [None]
        assert s.wantClass(Foo) is None
        assert s.wantClass(TestMe) == [None]

        s.tests = [ __file__ ]
        assert s.wantClass(Bar) == [None]
        assert s.wantClass(Foo) is None
        assert s.wantClass(TestMe)  == [None]
        
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
        c = Config()
        c.where = [absdir(os.path.join(os.path.dirname(__file__), 'support'))]
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

        s.tests = [ 'test.py', 'other/file.txt' ]
        assert s.wantFile('test.py')
        assert not s.wantFile('foo/test_foo.py')
        assert not s.wantFile('bar/baz/test.py', package='baz')
        # still not a python module... some plugin might want it,
        # but the default selector doesn't
        assert not s.wantFile('other/file.txt')

        s.tests = [ 'a.module' ]
        assert not s.wantFile('test.py')
        assert not s.wantFile('foo/test_foo.py')
        assert not s.wantFile('test-dir/test.py', package='baz')
        assert not s.wantFile('other/file.txt')
        assert s.wantFile('/path/to/a/module.py')
        assert s.wantFile('/another/path/to/a/module/file.py')
        assert not s.wantFile('/path/to/a/module/data/file.txt')
        
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

        s.tests = [ ':test_bar' ]
        assert s.wantFunction(test_bar)
        assert not s.wantFunction(test_foo)
        assert not s.wantFunction(foo)

        s.tests = [ __file__ ]
        assert s.wantFunction(test_bar)
        assert s.wantFunction(test_foo)
        assert not s.wantFunction(foo)

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

        s.tests = [ ':Baz.test_too' ]
        assert s.wantMethod(Baz.test_too)
        assert not s.wantMethod(Baz.test_me)                
        assert not s.wantMethod(Baz.other)

        s.tests = [ ':Baz' ]
        assert s.wantMethod(Baz.test_too)
        assert s.wantMethod(Baz.test_me)
        assert not s.wantMethod(Baz.other)

        s.tests = [ ':Spaz' ]
        assert not s.wantMethod(Baz.test_too)
        assert not s.wantMethod(Baz.test_me)
        assert not s.wantMethod(Baz.other)
        
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
        
        s.tests = [ 'this.that.another' ]
        assert not s.wantModule(m)
        assert s.wantModule(m2)
        assert s.wantModule(m3)
        assert s.wantModule(m4)        
        assert not s.wantModule(m5)
        assert not s.wantModule(m6)
        assert not s.wantModule(m7)
        assert not s.wantModule(m8)
        
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
        
        s.tests = [ 'this.that.another' ]
        assert not s.wantModuleTests(m)
        assert not s.wantModuleTests(m2)
        assert s.wantModuleTests(m3)
        assert s.wantModuleTests(m4)        
        assert not s.wantModuleTests(m5)
        assert not s.wantModuleTests(m6)
        assert not s.wantModuleTests(m7)
        assert not s.wantModuleTests(m8)

    def test_module_in_tests(self):
        s = Selector(Config())
        # s.tests = [ 'ever', 'what', 'what.ever' ]

        w = Mod('what')
        we = Mod('whatever')
        w_e = Mod('what.ever')
        w_n = Mod('what.not')
        f_e = Mod('for.ever')

        s.tests = [ 'what' ]
        assert s.moduleInTests(w)
        assert s.moduleInTests(w, True)        
        assert s.moduleInTests(w_e)
        assert s.moduleInTests(w_e, True)
        assert s.moduleInTests(w_n)
        assert s.moduleInTests(w_n, True)
        assert not s.moduleInTests(we)
        assert not s.moduleInTests(we, True)
        assert not s.moduleInTests(f_e)
        assert not s.moduleInTests(f_e, True)

        s.tests = [ 'what.ever' ]
        assert not s.moduleInTests(w)
        assert s.moduleInTests(w, True)        
        assert s.moduleInTests(w_e)
        assert s.moduleInTests(w_e, True)
        assert not s.moduleInTests(w_n)
        assert not s.moduleInTests(w_n, True)
        assert not s.moduleInTests(we)
        assert not s.moduleInTests(we, True)
        assert not s.moduleInTests(f_e)
        assert not s.moduleInTests(f_e, True)

        s.tests = [ 'what.ever', 'what.not' ]
        assert not s.moduleInTests(w)
        assert s.moduleInTests(w, True)        
        assert s.moduleInTests(w_e)
        assert s.moduleInTests(w_e, True)
        assert s.moduleInTests(w_n)
        assert s.moduleInTests(w_n, True)
        assert not s.moduleInTests(we)
        assert not s.moduleInTests(we, True)
        assert not s.moduleInTests(f_e)
        assert not s.moduleInTests(f_e, True)

    def test_module_in_tests_file(self):
        base = absdir(os.path.join(os.path.dirname(__file__), 'support'))
        c = Config()
        c.where = [base]
        s = Selector(c)

        f = Mod('foo', file=base+'/foo/__init__.pyc')
        t = Mod('test', path=base)
        f_t_f = Mod('foo.test_foo', path=base)
        d_t_t = Mod('test', path=base+'/test-dir')
        
        s.tests = [ 'test.py' ]
        assert not s.moduleInTests(f)
        assert s.moduleInTests(t)
        assert not s.moduleInTests(f_t_f)
        assert not s.moduleInTests(d_t_t)
        
        s.tests = [ 'foo/' ]
        assert s.moduleInTests(f)
        assert s.moduleInTests(f_t_f)
        assert not s.moduleInTests(t)
        assert not s.moduleInTests(d_t_t)

        s.tests = [ 'foo/test_foo.py' ]
        assert not s.moduleInTests(f)
        assert s.moduleInTests(f_t_f)
        assert not s.moduleInTests(t)
        assert not s.moduleInTests(d_t_t)
        
        s.tests = [ 'test-dir/test.py' ]
        assert not s.moduleInTests(f)
        assert not s.moduleInTests(t)
        assert not s.moduleInTests(f_t_f)
        assert s.moduleInTests(d_t_t)


        
if __name__ == '__main__':
    import logging
    logging.getLogger('nose.selector').setLevel(logging.DEBUG)
    logging.basicConfig()
    # log.setLevel(logging.DEBUG)
    unittest.main()
