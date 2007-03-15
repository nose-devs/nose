import unittest
import pdb
import sys
import nose.case
from nose.config import Config

class TestNoseCases(unittest.TestCase):

    def test_function_test_case(self):
        res = unittest.TestResult()
        
        a = []
        def func(a=a):
            a.append(1)

        case = nose.case.FunctionTestCase(func)
        case(res)
        assert a[0] == 1

    def test_method_test_case(self):
        res = unittest.TestResult()

        a = []
        class TestClass(object):
            def test_func(self, a=a):
                a.append(1)

        case = nose.case.MethodTestCase(TestClass.test_func)
        case(res)
        assert a[0] == 1

    def test_method_test_case_fixtures(self):        
        res = unittest.TestResult()
        called = []
        class TestClass(object):
            def setup(self):
                called.append('setup')
            def teardown(self):
                called.append('teardown')
            def test_func(self):
                called.append('test')

        case = nose.case.MethodTestCase(TestClass.test_func)
        case(res)
        self.assertEqual(called, ['setup', 'test', 'teardown'])

        class TestClassFailingSetup(TestClass):
            def setup(self):
                called.append('setup')
                raise Exception("failed")
        called[:] = []
        case = nose.case.MethodTestCase(TestClassFailingSetup.test_func)
        case(res)
        self.assertEqual(called, ['setup'])        

        class TestClassFailingTest(TestClass):
            def test_func(self):
                called.append('test')
                raise Exception("failed")
            
        called[:] = []
        case = nose.case.MethodTestCase(TestClassFailingTest.test_func)
        case(res)
        self.assertEqual(called, ['setup', 'test', 'teardown'])     
        
    def test_function_test_case_fixtures(self):
        from nose.tools import with_setup
        res = unittest.TestResult()

        called = {}

        def st():
            called['st'] = True
        def td():
            called['td'] = True

        def func_exc():
            called['func'] = True
            raise TypeError("An exception")

        func_exc = with_setup(st, td)(func_exc)
        case = nose.case.FunctionTestCase(func_exc)
        case(res)
        assert 'st' in called
        assert 'func' in called
        assert 'td' in called

    def test_failure_case(self):
        res = unittest.TestResult()
        f = nose.case.Failure(ValueError, "a is not b")
        f(res)
        assert res.errors


class TestNoseTestWrapper(unittest.TestCase):
    def test_case_fixtures_called(self):
        """Instance fixtures are properly called for wrapped tests"""
        res = unittest.TestResult()
        called = []
                        
        class TC(unittest.TestCase):
            def setUp(self):
                print "TC setUp %s" % self
                called.append('setUp')
            def runTest(self):
                print "TC runTest %s" % self
                called.append('runTest')
            def tearDown(self):
                print "TC tearDown %s" % self
                called.append('tearDown')

        case = nose.case.Test(TC())
        case(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures
        self.assertEqual(called, ['setUp', 'runTest', 'tearDown'])

    def test_result_proxy_used(self):
        """A result proxy is used to wrap the result for all tests"""
        class TC(unittest.TestCase):
            def runTest(self):
                raise Exception("error")
            
        class ResPrxFactory:
            def __call__(self, result, test):
                return ResPrx(result, test)

        class ResPrx:
            called = []
            def __init__(self, result, test):
                self.result = result
                self.test = test
                assert isinstance(test, nose.case.Test), \
                       "%s (%s) is not a nose.case.Test" % (test, type(test))
            def startTest(self, test):
                print "proxy startTest"
                assert test is self.test.test, \
                       "%s<%s:%s> is not %s<%s:%s>" \
                       % (test, test.__class__, id(test),
                          self.test.test,
                          self.test.test.__class__,
                          id(self.test.test))
                self.called.append(('startTest', test))
            def stopTest(self, test):
                print "proxy stopTest"
                assert test is self.test.test, \
                       "%s<%s:%s> is not %s<%s:%s>" \
                       % (test, test.__class__, id(test),
                          self.test.test,
                          self.test.test.__class__,
                          id(self.test.test))
                self.called.append(('stopTest', test))
            def addError(self, test, err):
                print "proxy addError"
                assert test is self.test.test, \
                       "%s<%s:%s> is not %s<%s:%s>" \
                       % (test, test.__class__, id(test),
                          self.test.test,
                          self.test.test.__class__,
                          id(self.test.test))
                self.called.append(('addError', test, err))
            def addSuccess(self, test):
                assert False, \
                       "addSuccess was called for %s (%s)" % test
                
        res = unittest.TestResult()
        config = Config()
        config.resultProxy = ResPrxFactory()
        case = nose.case.Test(TC(), config=config)

        case(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

        # NOTE this is currently failiing because the wrapper is
        # issuing duplicate calls to the result.
        calls = [ c[0] for c in ResPrx.called ]
        self.assertEqual(calls, ['startTest', 'addError', 'stopTest'])

        
if __name__ == '__main__':
    unittest.main()
