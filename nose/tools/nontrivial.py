"""Tools not exempt from being descended into in tracebacks"""

from __future__ import with_statement

import time


__all__ = ['make_decorator', 'raises', 'set_trace', 'timed', 'with_setup',
           'TimeExpired', 'istest', 'nottest']


class TimeExpired(AssertionError):
    pass


def make_decorator(func):
    """
    Wraps a test decorator so as to properly replicate metadata
    of the decorated function, including nose's additional stuff
    (namely, setup and teardown).
    """
    def decorate(newfunc):
        if hasattr(func, 'compat_func_name'):
            name = func.compat_func_name
        else:
            name = func.__name__
        newfunc.__dict__ = func.__dict__
        newfunc.__doc__ = func.__doc__
        newfunc.__module__ = func.__module__
        if not hasattr(newfunc, 'compat_co_firstlineno'):
            newfunc.compat_co_firstlineno = func.func_code.co_firstlineno
        try:
            newfunc.__name__ = name
        except TypeError:
            # can't set func name in 2.3
            newfunc.compat_func_name = name
        return newfunc
    return decorate


class raises(object):
    """Test must raise one of expected exceptions to pass.

    Example use::

      @raises(TypeError, ValueError)
      def test_raises_type_error():
          raise TypeError("This test passes")

      @raises(Exception)
      def test_that_fails_by_passing():
          pass


      def check_value_error(e):
          assert e.message == "ouch!"

      with raises(ValueError, checker=check_value_error):
          raise ValueError("ouch!")

      @raises(ValueError, checker=check_value_error)
      def test_for_ouch_typeerror():
          raise ValueError("ouch!")


      @raises(ValueError, TypeError, name="test_custom")
      def test_custom_with_long_name():
          raise TypeError

    If you wish to test many assertions about exceptions in a single test,
    you maybe need to use `assert_raises` instead of this.
    """

    def __init__(self, *exceptions, **kwargs):
        self.exceptions = exceptions
        self.name = kwargs.pop("name", None)
        self.checker = kwargs.pop("checker", None)

    def __call__(self, func):
        """Work as a decorator."""
        def newfunc(*arg, **kw):
            self.name = self.name or func.__name__
            with self:
                func(*arg, **kw)
        newfunc = make_decorator(func)(newfunc)
        return newfunc

    def __enter__(self):
        self.name = self.name or "context"
        return self

    def __exit__(self, error_type, error, traceback):
        if not error:
            valid = ' or '.join([e.__name__ for e in self.exceptions])
            message = "%s() did not raise %s" % (self.name, valid)
            raise AssertionError(message)
        elif error_type in self.exceptions:
            self.check_exception(error)
            return True
        else:
            return None  # raise it

    def check_exception(self, error):
        """Checks a exception if the check exist."""
        if self.checker:
            do_check = self.checker
            do_check(error)


def set_trace():
    """Call pdb.set_trace in the calling frame, first restoring
    sys.stdout to the real output stream. Note that sys.stdout is NOT
    reset to whatever it was before the call once pdb is done!
    """
    import pdb
    import sys
    stdout = sys.stdout
    sys.stdout = sys.__stdout__
    pdb.Pdb().set_trace(sys._getframe().f_back)
    

def timed(limit):
    """Test must finish within specified time limit to pass.

    Example use::

      @timed(.1)
      def test_that_fails():
          time.sleep(.2)
    """
    def decorate(func):
        def newfunc(*arg, **kw):
            start = time.time()
            func(*arg, **kw)
            end = time.time()
            if end - start > limit:
                raise TimeExpired("Time limit (%s) exceeded" % limit)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate


def with_setup(setup=None, teardown=None):
    """Decorator to add setup and/or teardown methods to a test function::

      @with_setup(setup, teardown)
      def test_something():
          " ... "

    Note that `with_setup` is useful *only* for test functions, not for test
    methods or inside of TestCase subclasses.
    """
    def decorate(func, setup=setup, teardown=teardown):
        if setup:
            if hasattr(func, 'setup'):
                _old_s = func.setup
                def _s():
                    setup()
                    _old_s()
                func.setup = _s
            else:
                func.setup = setup
        if teardown:
            if hasattr(func, 'teardown'):
                _old_t = func.teardown
                def _t():
                    _old_t()
                    teardown()
                func.teardown = _t
            else:
                func.teardown = teardown
        return func
    return decorate


def istest(func):
    """Decorator to mark a function or method as a test
    """
    func.__test__ = True
    return func


def nottest(func):
    """Decorator to mark a function or method as *not* a test
    """
    func.__test__ = False
    return func
