import unittest
import nose.selector
import test_selector
from nose.config import Config
from nose.plugins.base import Plugin

class TestSelectorPlugins(unittest.TestCase):

    def test_null_selector(self):
        # run the test_selector.TestSelector tests with
        # a null selector config'd in, should still all pass
        class NullSelector(Plugin):
            pass


    def test_rejection(self):
        class EvilSelector(Plugin):
            def wantFile(self, filename, package=None):
                if 'good' in filename:
                    return False
                return None

        c = Config()
        c.plugins = [ EvilSelector() ]
        s = nose.selector.Selector(c)
        s2 = nose.selector.Selector(Config())
        
        assert s.wantFile('test_neutral.py')
        assert s2.wantFile('test_neutral.py')
        
        assert s.wantFile('test_evil.py')
        assert s2.wantFile('test_evil.py')
        
        assert not s.wantFile('test_good.py')
        assert s2.wantFile('test_good.py')
        
if __name__ == '__main__':
    unittest.main()
