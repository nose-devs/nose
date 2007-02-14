import unittest
from loader import TestLoader

class TestTestLoader(unittest.TestCase):

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
        
if __name__ == '__main__':
    unittest.main()
