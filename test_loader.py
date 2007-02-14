import os
import unittest
from loader import TestLoader

# Mock the filesystem access so we don't have to maintain
# a support dir with real files
_listdir = os.listdir
_isdir = os.path.isdir
_isfile = os.path.isfile

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


class TestTestLoader(unittest.TestCase):

    def setUp(self):
        os.listdir = mock_listdir
        os.path.isdir = mock_isdir
        os.path.isfile = mock_isfile

    def tearDown(self):
        os.listdir = _listdir
        os.path.isdir = _isdir
        os.path.isfile = _isfile

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

    def test_load_from_name_function(self):        
        l = TestLoader()
        suite = l.loadTestsFromName(':test_func')
        tests = [t for t in suite]
        assert tests
        
if __name__ == '__main__':
    unittest.main()
