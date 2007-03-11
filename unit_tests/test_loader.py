import imp
import os
import sys
import unittest
from nose.loader import TestLoader

# FIXME replace with nose importer eventually
from nose import loader # so we can set its __import__
from nose import context  # so we can set its __import__
from nose import util # so we can set its __import__
import nose.case

#
# Setting up the fake modules that we'll use for testing
# test loading
#
M = {}
M['test_module'] = imp.new_module('test_module')
M['module'] = imp.new_module('module')
M['package'] = imp.new_module('package')
M['package'].__path__ = ['/package']
M['package'].__file__ = '/package/__init__.py'
M['package.subpackage'] = imp.new_module('package.subpackage')
M['package'].subpackage = M['package.subpackage']
M['package.subpackage'].__path__ = ['/package/subpackage']
M['package.subpackage'].__file__ = '/package/subpackage/__init__.py'
M['test_module_with_generators'] = imp.new_module('test_module_with_generators')


# a unittest testcase subclass
class TC(unittest.TestCase):
    def runTest(self):
        pass

class TC2(unittest.TestCase):
    def runTest(self):
        pass
    
# test function
def test_func():
    pass

# non-testcase-subclass test class
class TestClass:
    
    def test_func(self):
        pass
    
    def test_generator_inline(self):
        """docstring for test generator inline
        """
        def test_odd(v):
            assert v % 2
        for i in range(0, 4):
            yield test_odd, i
            
    def test_generator_method(self):
        """docstring for test generator method
        """
        for i in range(0, 4):
            yield self.try_odd, i
            
    def test_generator_method_name(self):
        """docstring for test generator method name
        """
        for i in range(0, 4):
            yield 'try_odd', i
            
    def try_odd(self, v):
        assert v % 2

# test function that is generator
def test_func_generator():
    """docstring for test func generator
    """
    def test_odd(v):
        assert v % 2
    for i in range(0, 4):
        yield test_odd, i

def test_func_generator_name():
    """docstring for test func generator name
    """
    for i in range(0, 4):
        yield 'try_odd', i

def try_odd(v):
    assert v % 2

M['nose'] = nose
M['__main__'] = sys.modules['__main__']
M['test_module'].TC = TC
TC.__module__ = 'test_module'
M['test_module'].test_func = test_func
test_func.__module__ = 'test_module'
M['module'].TC2 = TC2
TC2.__module__ = 'module'
M['test_module_with_generators'].TestClass = TestClass
TestClass.__module__ = 'test_module_with_generators'
M['test_module_with_generators'].test_func_generator = test_func_generator
M['test_module_with_generators'].test_func_generator_name = \
    test_func_generator_name
M['test_module_with_generators'].try_odd = try_odd
test_func_generator_name.__module__ = 'test_module_with_generators'
test_func_generator.__module__ = 'test_module_with_generators'
try_odd.__module__ = 'test_module_with_generators'
del TC
del TC2
del test_func
del TestClass
del test_func_generator

# sys.modules.update(M)

# Mock the filesystem access so we don't have to maintain
# a support dir with real files
_listdir = os.listdir
_isdir = os.path.isdir
_isfile = os.path.isfile
_import = __import__


#
# Mock functions
#
def mock_listdir(path):
    if path.endswith('/package'):
        return ['.', '..', 'subpackage', '__init__.py']
    elif path.endswith('/subpackage'):
        return ['.', '..', '__init__.py']
    return ['.', '..', 'test_module.py', 'module.py']


def mock_isdir(path):
    print "is dir '%s'?" % path
    if path in ('/a/dir/path', '/package', '/package/subpackage'):
        return True
    return False


def mock_isfile(path):
    if path in ('.', '..'):
        return False
    return '.' in path


def mock_import(modname, gl=None, lc=None, fr=None):
    if gl is None:
        gl = M
    if lc is None:
        lc = locals()
    try:
        mod = sys.modules[modname]
    except KeyError:
        pass
    try:
        pname = []
        for part in modname.split('.'):
            pname.append(part)
            mname = '.'.join(pname)
            mod = gl[mname]
            sys.modules[mname] = mod
        return mod
    except KeyError:
        raise ImportError("No '%s' in fake module list" % modname)
    
#
# Tests
#
class TestTestLoader(unittest.TestCase):

    def setUp(self):
        os.listdir = mock_listdir
        os.path.isdir = mock_isdir
        os.path.isfile = mock_isfile
        loader.__import__ = context.__import__ = util.__import__ = mock_import
        
    def tearDown(self):
        os.listdir = _listdir
        os.path.isdir = _isdir
        os.path.isfile = _isfile
        loader.__import__ = context.__import__ = util.__import__ = __import__

    def test_lint(self):
        """Test that main API functions exist
        """
        l = TestLoader()
        l.loadTestsFromTestCase
        l.loadTestsFromModule
        l.loadTestsFromName
        l.loadTestsFromNames

    def test_loader_has_context(self):
        l = TestLoader()
        assert l.context

        l = TestLoader(context='whatever')
        self.assertEqual(l.context, 'whatever')

    def test_load_from_name_dir_abs(self):
        l = TestLoader()
        suite = l.loadTestsFromName('/a/dir/path')
        tests = [t for t in suite]
        self.assertEqual(len(tests), 1)

    def test_load_from_name_module_filename(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module.py')
        tests = [t for t in suite]
        assert tests

    def test_load_from_name_module(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module')
        tests = [t for t in suite]
        assert tests            

    def test_load_from_name_nontest_module(self):        
        l = TestLoader()
        suite = l.loadTestsFromName('module')
        tests = [t for t in suite]
        assert tests

    def test_load_from_name_method(self):
        res = unittest.TestResult()
        l = TestLoader()
        suite = l.loadTestsFromName(':TC.runTest')
        tests = [t for t in suite]
        assert tests
        for test in tests:
            test(res)
        assert not res.errors, "Got errors %s running tests" % res.errors

    def test_load_from_name_module_class(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:TC')
        tests = [t for t in suite]
        assert tests
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests
        assert filter(lambda t: t.context, tests)

    def test_load_from_name_module_func(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:test_func')
        tests = [t for t in suite]
        assert tests
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests
        assert isinstance(tests[0].test, nose.case.FunctionTestCase), \
               "Expected FunctionTestCase not %s" % tests[0].test

    def test_load_from_name_module_method(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:TC.runTest')
        tests = [t for t in suite]
        assert tests
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests

    def test_load_from_name_module_missing_class(self):
        res = unittest.TestResult()
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:TC2')
        tests = [t for t in suite]
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests
        tests[0](res)
        assert res.errors, "Expected missing class test to raise exception"

    def test_load_from_name_module_missing_func(self):
        res = unittest.TestResult()
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:test_func2')
        tests = [t for t in suite]
        assert len(tests) == 1, \
               "Should have loaded 0 test, but got %s" % tests
        tests[0](res)
        assert res.errors, "Expected missing func test to raise exception"

    def test_load_from_name_module_missing_method(self):
        res = unittest.TestResult()
        l = TestLoader()
        suite = l.loadTestsFromName('test_module:TC.testThat')
        tests = [t for t in suite]
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests
        tests[0](res)
        assert res.errors, "Expected missing method test to raise exception"

    def test_load_from_name_missing_module(self):
        res = unittest.TestResult()
        l = TestLoader()
        suite = l.loadTestsFromName('other_test_module')
        tests = [t for t in suite]
        assert len(tests) == 1, \
               "Should have loaded 1 test, but got %s" % tests
        tests[0](res)
        assert res.errors, "Expected missing module test to raise exception"

    def test_cases_from_testcase_have_context(self):
        test_module = M['test_module']
        l = TestLoader()
        suite = l.loadTestsFromTestCase(test_module.TC)
        print suite
        tests = [t for t in suite]
        for test in tests:
            assert hasattr(test, 'context'), "Test %s has no context" % test

    def test_load_test_func(self):
        l = TestLoader()
        suite = l.loadTestsFromName('test_module')
        tests = [t for t in suite]
        self.assertEqual(len(tests), 2, "Wanted 2 tests, got %s" % tests)
        assert filter(lambda t: t.context, tests)
        print tests
        class_tests = tests[0]
        func_tests = tests[1:]
        assert class_tests, \
               "Expected class suite got %s" % class_tests
        assert len(func_tests) == 1, \
               "Expected 1 func test got %s" % func_tests
        for test in class_tests:
            assert test.context
            assert isinstance(test.test, unittest.TestCase), \
                   "Expected TestCase npt %s" % tests[0].test
        for test in func_tests:
            assert test.context
            assert isinstance(test.test, nose.case.FunctionTestCase), \
                   "Expected FunctionTestCase not %s" % tests[1].test

    def test_load_from_name_package_root_path(self):
        l = TestLoader()
        suite = l.loadTestsFromName('/package')
        print suite
        tests = [t for t in suite]
        assert len(tests) == 1, "Expected one test, got %s" % tests
        tests = list(tests[0])
        assert not tests, "The full test list %s was not empty" % tests

    def test_load_from_name_subpackage_path(self):
        l = TestLoader()
        suite = l.loadTestsFromName('/package/subpackage')
        print suite
        tests = [t for t in suite]
        assert len(tests) == 0, "Expected no tests, got %s" % tests

    def test_load_generators(self):
        test_module_with_generators = M['test_module_with_generators']
        l = TestLoader()
        suite = l.loadTestsFromModule(test_module_with_generators)
        tests = [t for t in suite]

        for t in tests:
            assert isinstance(t, unittest.TestSuite), \
                   "Test %s is not a suite" % t

        # the first item is a class, with both normal and generator methods
        count = 0
        cl_tests = [t for t in tests[0]]
        normal, gens = cl_tests[0], cl_tests[1:]
        assert isinstance(normal, nose.case.Test), \
               "Expected a test case but got %s" % normal
        for gen in gens:
            assert isinstance(gen, unittest.TestSuite), \
                   "Expected a generator test suite, but got %s" % gen
            count = 0
            for t in gen:
                print "generated test %s" % t
                print t.shortDescription()
                assert isinstance(t, nose.case.Test), \
                       "Test %s is not a test?" % t
                count += 1
            self.assertEqual(count, 4, "Expected to generate 4 tests, but "
                             "got %s from %s" % (count, gen))
            
        # 2nd item is generated from test_func_generator
        count = 0
        for t in tests[1]:
            print "generated test %s" % t
            print t.shortDescription()
            assert isinstance(t, nose.case.Test), \
                   "Test %s is not a Test?" % t
            assert isinstance(t.test, nose.case.FunctionTestCase), \
                   "Test %s is not a FunctionTestCase" % t.test
            assert 'test_func_generator' in str(t), \
                   "Bad str val '%s' for test" % str(t)
            assert 'docstring for test func generator' \
                   in t.shortDescription(), \
                   "Bad shortDescription '%s' for test %s" % \
                   (t.shortDescription(), t)
            count += 1
        assert count == 4, \
               "Expected to generate 4 tests, but got %s" % count

        count = 0
        for t in tests[2]:
            print "generated test %s" % t
            print t.shortDescription()
            assert isinstance(t, nose.case.Test), \
                   "Test %s is not a Test?" % t
            assert isinstance(t.test, nose.case.FunctionTestCase), \
                   "Test %s is not a FunctionTestCase" % t.test
            assert 'test_func_generator_name' in str(t), \
                   "Bad str val '%s' for test" % str(t)
            assert 'docstring for test func generator name' \
                   in t.shortDescription(), \
                   "Bad shortDescription '%s' for test %s" % \
                   (t.shortDescription(), t)
            count += 1
        assert count == 4, \
               "Expected to generate 4 tests, but got %s" % count
        
if __name__ == '__main__':
    unittest.main()
