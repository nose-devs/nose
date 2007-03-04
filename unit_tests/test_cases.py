import unittest
import pdb
import sys
import nose.case
from nose.context import FixtureContext

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
    def test_context_case_fixtures(self):
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

        context = FixtureContext()
        case = context(TC())
        case(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures
        self.assertEqual(called, ['setUp', 'runTest', 'tearDown'])

    def test_context_case_result_proxy(self):
        class TC(unittest.TestCase):
            def runTest(self):
                raise Exception("error")
            

        class ResPrx:
            def __init__(self):
                self.called = []
            def __call__(self, result):
                print "Called %s" % result
                self.result = result
                return self
            def startTest(self, test):
                print "proxy startTest"
                self.called.append(('startTest', test))
            def stopTest(self, test):
                print "proxy stopTest"
                self.called.append(('stopTest', test))
            def addError(self, test, err):
                print "proxy addError"
                self.called.append(('addError', test, err))
            def addSuccess(self, test):
                pass                     
                
        res = unittest.TestResult()
        proxy = ResPrx()
        context = FixtureContext(result_proxy=proxy)
        case = context(TC())

        case(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

        # NOTE this is currently failiing because the wrapper is
        # issuing duplicate calls to the result.
        calls = [ c[0] for c in proxy.called ]
        self.assertEqual(calls, ['startTest', 'addError', 'stopTest'])

        
if __name__ == '__main__':
    unittest.main()
