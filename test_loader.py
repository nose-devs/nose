import imp
import os
import sys
import unittest
from loader import TestLoader

# FIXME replace with nose importer eventually
import loader # so we can set its __import__
from nose import fixture  # so we can set its __import__

#
# Setting up the fake modules that we'll use for testing
# test loading
#
test_module = imp.new_module('test_module')
module = imp.new_module('module')

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

# FIXME non-testcase-subclass test class

test_module.TC = TC
TC.__module__ = 'test_module'
test_module.test_func = test_func
test_func.__module__ = 'test_module'
module.TC2 = TC2
TC2.__module__ = 'module'
del TC
del TC2
del test_func

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
    return ['.', '..', 'test_module.py', 'module.py']


def mock_isdir(path):
    if path == '/a/dir/path':
        return True
    return False


def mock_isfile(path):
    if path in ('.', '..'):
        return False
    return '.' in path


def mock_import(modname, gl=None, lc=None, fr=None):
    if gl is None:
        gl = globals()
    if lc is None:
        lc = locals()
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    try:
        mod = gl[modname]
        sys.modules[modname] = mod
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
        loader.__import__ = fixture.__import__ = mock_import
        
    def tearDown(self):
        os.listdir = _listdir
        os.path.isdir = _isdir
        os.path.isfile = _isfile
        loader.__import__ = fixture.__import__ = __import__

    def test_lint(self):
        """Test that main API functions exist
        """
        l = TestLoader()
        l.loadTestsFromTestCase
        l.loadTestsFromModule
        l.loadTestsFromName
        l.loadTestsFromNames
        
    def test_load_from_names_is_lazy(self):
        l = TestLoader()
        l.loadTestsFromName = lambda self, name, module: self.fail('not lazy')
        l.loadTestsFromNames(['a', 'b', 'c'])

    def test_loader_has_context(self):
        l = TestLoader()
        assert l.context

        l = TestLoader('whatever')
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
        l = TestLoader()
        suite = l.loadTestsFromName(':TC.test')
        tests = [t for t in suite]
        assert tests

    def test_cases_from_testcase_have_context(self):
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
        
if __name__ == '__main__':
    unittest.main()
