import sys
import time
import unittest
from nose.tools import *

compat_24 =  sys.version_info >= (2, 4)

class TestTools(unittest.TestCase):

    def test_ok(self):
        ok_(True)
        try:
            ok_(False, "message")
        except AssertionError, e:
            assert str(e) == "message"
        else:
            self.fail("ok_(False) did not raise assertion error")

    def test_eq(self):
        eq_(1, 1)
        try:
            eq_(1, 0, "message")
        except AssertionError, e:
            assert str(e) == "message"
        else:
            self.fail("eq_(1, 0) did not raise assertion error")
        try:
            eq_(1, 0)
        except AssertionError, e:
            assert str(e) == "1 != 0"
        else:
            self.fail("eq_(1, 0) did not raise assertion error")

    def test_raises(self):
        from nose.case import FunctionTestCase
        
        def raise_typeerror():
            raise TypeError("foo")

        def noraise():
            pass
        
        raise_good = raises(TypeError)(raise_typeerror)
        raise_other = raises(ValueError)(raise_typeerror)
        no_raise = raises(TypeError)(noraise)

        tc = FunctionTestCase(raise_good)
        self.assertEqual(str(tc), "%s.%s" % (__name__, 'raise_typeerror'))
        
        raise_good()
        try:
            raise_other()
        except TypeError, e:
            pass
        else:
            self.fail("raises did pass through unwanted exception")

        try:
            no_raise()
        except AssertionError, e:
            pass
        else:
            self.fail("raises did not raise assertion error on no exception")

    def test_timed(self):

        def too_slow():
            time.sleep(.3)
        too_slow = timed(.2)(too_slow)
            
        def quick():
            time.sleep(.1)
        quick = timed(.2)(quick)

        quick()
        try:
            too_slow()
        except TimeExpired:
            pass
        else:
            self.fail("Slow test did not throw TimeExpired")

    def test_make_decorator(self):
        def func():
            pass
        func.setup = 'setup'
        func.teardown = 'teardown'

        def f1():
            pass
        
        f2 = make_decorator(func)(f1)
        
        assert f2.setup == 'setup'
        assert f2.teardown == 'teardown'

    def test_nested_decorators(self):
        from nose.tools import raises, timed, with_setup
        
        def test():
            pass
        
        def foo():
            pass
        
        test = with_setup(foo, foo)(test)
        test = timed(1.0)(test)
        test = raises(TypeError)(test)
        assert test.setup == foo
        assert test.teardown == foo

    def test_decorator_func_sorting(self):
        from nose.tools import raises, timed, with_setup
        from nose.util import func_lineno
        
        def test1():
            pass

        def test2():
            pass

        def test3():
            pass

        def foo():
            pass

        test1_pos = func_lineno(test1)
        test2_pos = func_lineno(test2)
        test3_pos = func_lineno(test3)

        test1 = raises(TypeError)(test1)
        test2 = timed(1.0)(test2)
        test3 = with_setup(foo)(test3)

        self.assertEqual(func_lineno(test1), test1_pos)
        self.assertEqual(func_lineno(test2), test2_pos)
        self.assertEqual(func_lineno(test3), test3_pos)
        
    def test_testcase_funcs(self):
        import nose.tools
        tc_asserts = [ at for at in dir(nose.tools)
                       if at.startswith('assert_') ]
        print tc_asserts
        
        # FIXME: not sure which of these are in all supported
        # versions of python
        assert 'assert_raises' in tc_asserts
        if compat_24:
            assert 'assert_true' in tc_asserts

            
if __name__ == '__main__':
    unittest.main()
