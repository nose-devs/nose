import unittest
import pdb
import sys
import nose.case

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

        case = nose.case.MethodTestCase(TestClass, 'test_func')
        case(res)
        assert a[0] == 1

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
        
if __name__ == '__main__':
    unittest.main()
