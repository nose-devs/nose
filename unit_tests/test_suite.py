from nose.config import Config
from nose import case
from nose.suite import LazySuite, ContextSuite, ContextSuiteFactory
#from nose.context import FixtureContext
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

    def test_tests_are_wrapped(self):
        """Tests in a context suite are wrapped"""
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')])
        for test in suite:
            assert isinstance(test.test, self.TC)

    def test_nested_context_suites(self):
        """Nested suites don't re-wrap"""
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')])
        suite2 = ContextSuite(suite)
        suite3 = ContextSuite([suite2])

        # suite3 is [suite2]
        tests = [t for t in suite3]
        assert isinstance(tests[0], ContextSuite)
        # suite2 is [suite]
        tests = [t for t in tests[0]]
        assert isinstance(tests[0], ContextSuite)
        # suite is full of wrapped tests
        tests = [t for t in tests[0]]
        cases = filter(lambda t: isinstance(t, case.Test), tests)
        assert cases
        assert len(cases) == len(tests)

    def test_context_fixtures_called(self):
        class P:
            was_setup = False
            was_torndown = False
            def setup(self):
                self.was_setup = True

            def teardown(self):
                self.was_torndown = True

        parent = P()
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            parent=parent)
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
        suite = ContextSuite(
            [self.TC('test_one'), self.TC('test_two')],
            parent=parent)
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
        suite = ContextSuite([], parent=parent)
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
        
