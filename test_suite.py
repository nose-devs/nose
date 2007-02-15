from suite import LazySuite, ContextSuite, ContextSuiteFactory
from nose.fixture import Context
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

class TestContextSuite(unittest.TestCase):

    def setUp(self):
        class TC(unittest.TestCase):
            def test_one(self):
                pass
            def test_two(self):
                pass
        self.TC = TC

    def test_tests_get_context(self):
        """Tests in a context suite have a context"""
        ctx = Context()
        suite = ContextSuite(
            lambda: [self.TC('test_one'), self.TC('test_two')],
            ctx)
        for test in suite:
            assert test.context is ctx

    def test_nested_context_suites(self):
        """Nested suites don't recontextualize"""
        ctx = Context()
        suite = ContextSuite(
            lambda: [self.TC('test_one'), self.TC('test_two')],
            ctx)
        top_suite = ContextSuite(lambda: suite, ctx)
        for test in top_suite:
            assert not hasattr(test.test, 'context'), \
                   "The test %s wraps %s which has a context" \
                   % (test, test.test)
        

if __name__ == '__main__':
    unittest.main()
        
