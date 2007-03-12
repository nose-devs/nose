from nose.config import Config
from nose import case
from nose.suite import LazySuite, ContextSuite, ContextSuiteFactory
#from nose.context import FixtureContext
import unittest
from mock import MockContext

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


    def test_lazy_and_nonlazy(self):
        TC = self.TC
        tests = [TC('test_one'), TC('test_two')]
        def gen_tests():
            for test in tests:
                yield test

        nonlazy = LazySuite(tests)
        lazy = LazySuite(gen_tests)

        assert lazy
        assert nonlazy

        lazytests = []
        nonlazytests = []
        for t in lazy:
            print "lazy %s" % t
            lazytests.append(t)
        for t in nonlazy:
            print "nonlazy %s" % t
            nonlazytests.append(t)
        slazy = map(str, lazytests)
        snonlazy = map(str, nonlazytests)
        assert slazy == snonlazy, \
               "Lazy and Nonlazy produced different test lists (%s vs %s)" \
               % (slazy, snonlazy)

    def test_lazy_nonzero(self):
        """__nonzero__ works correctly for lazy suites"""
        
        TC = self.TC
        tests = [TC('test_one'), TC('test_two')]
        def gen_tests():
            for test in tests:
                yield test

        lazy = LazySuite(gen_tests)
        assert lazy
        assert lazy
        assert lazy

        count = 0
        for test in lazy:
            print test
            assert test
            count += 1
        self.assertEqual(count, 2, "Expected 2 tests, got %s" % count)
        assert lazy

        def gen_tests_empty():
            for test in []:
                yield test
            return
        empty = LazySuite(gen_tests_empty)
        assert not empty
        for test in empty:
            assert False, "Loaded a test from empty suite: %s" % test

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
        ctx = MockContext()
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            ctx)
        for test in suite:
            assert test.context is ctx

    def test_nested_context_suites(self):
        """Nested suites don't recontextualize"""
        ctx = MockContext()
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            ctx)
        top_suite = ContextSuite(suite, ctx)
        for test in top_suite:
            if hasattr(test, 'test'):
                assert not hasattr(test.test, 'context'), \
                       "The test %s wraps %s which has a context" \
                       % (test, test.test)
            elif isinstance(test, unittest.TestSuite):
                for t in test:
                    if hasattr(t, 'test'):
                        assert not hasattr(t.test, 'context'), \
                               "The test %s wraps %s which has a context" \
                               % (t, t.test)

    def test_context_fixtures_called(self):
        class P:
            was_setup = False
            was_torndown = False
            def setup(self):
                self.was_setup = True

            def teardown(self):
                self.was_torndown = True

        parent = P()
        ctx = MockContext(parent)
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            ctx)
        res = unittest.TestResult()
        suite(res)

        assert not res.errors, res.errors
        assert not res.failures, res.failures
        assert parent.was_setup
        assert parent.was_torndown

    def test_context_fixtures_setup_fails(self):
        class P:
            was_setup = False
            was_torndown = False
            def setup(self):
                self.was_setup = True
                assert False, "Setup failed"

            def teardown(self):
                self.was_torndown = True

        parent = P()
        ctx = MockContext(parent)
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            ctx)
        res = unittest.TestResult()
        suite(res)

        assert not res.failures, res.failures
        assert res.errors, res.errors
        assert parent.was_setup
        assert not parent.was_torndown
        assert res.testsRun == 0, \
               "Expected to run no tests but ran %s" % res.testsRun

    def test_context_fixtures_no_tests_no_setup(self):
        class P:
            was_setup = False
            was_torndown = False
            def setup(self):
                self.was_setup = True

            def teardown(self):
                self.was_torndown = True

        parent = P()
        ctx = MockContext(parent)
        suite = ContextSuite([], ctx)
        res = unittest.TestResult()
        suite(res)

        assert not res.failures, res.failures
        assert not res.errors, res.errors
        assert not parent.was_setup
        assert not parent.was_torndown
        assert res.testsRun == 0, \
               "Expected to run no tests but ran %s" % res.testsRun

if __name__ == '__main__':
    unittest.main()
        
