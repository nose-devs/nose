from suite import LazySuite
import unittest

class TestLazySuite(unittest.TestCase):

    def setUp(self):
        class TC(unittest.TestCase):
            def test_one(self):
                pass
            def test_two(self):
                pass
        self.TC = TC
    def test_test_generator(self):
        TC = self.TC
        tests = [TC('test_one'), TC('test_two')]
        def gen_tests():
            for test in tests:
                yield test
        suite = LazySuite(gen_tests)
        self.assertEqual(list([test for test in suite]), tests)

if __name__ == '__main__':
    unittest.main()
        
