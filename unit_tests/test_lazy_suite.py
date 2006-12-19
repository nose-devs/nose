import unittest
from nose import LazySuite
from helpers import iter_compat

def gen():
    for x in range(0, 10):
        yield TestLazySuite.TC('test')

class TestLazySuite(unittest.TestCase):

    class TC(unittest.TestCase):
        def test(self):
            pass
        
    def test_basic_iteration(self):        
        ls = LazySuite(gen)
        for t in iter_compat(ls):
            assert isinstance(t, unittest.TestCase)
            
    def test_setup_teardown(self):                
        class SetupTeardownLazySuite(LazySuite):
            _setup = False
            _teardown = False
            
            def setUp(self):
                self._setup = True

            def tearDown(self):
                if self._setup:
                    self._teardown = True

        class Result:
            shouldStop = False

            def addSuccess(self, test):
                pass
            
            def startTest(self, test):
                pass
            
            def stopTest(self, test):
                pass
            
        ls = SetupTeardownLazySuite(gen)
        ls(Result())
        assert ls._setup
        assert ls._teardown
        
if __name__ == '__main__':
    unittest.main()
