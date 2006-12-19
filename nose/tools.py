"""
Tools for testing
-----------------

nose.tools provides a few convenience functions to make writing tests
easier. You don't have to use them; nothing in the rest of nose depends
on any of these methods.
"""
import time


class TimeExpired(AssertionError):
    pass

def ok_(expr, msg=None):
    """Shorthand for assert. Saves 3 whole characters!
    """
    assert expr, msg

def eq_(a, b, msg=None):
    """Shorthand for 'assert a == b, "%r != %r" % (a, b)
    """
    assert a == b, msg or "%r != %r" % (a, b)

def make_decorator(func):
    """
    Wraps a test decorator so as to properly replicate metadata
    of the decorated function, including nose's additional stuff
    (namely, setup and teardown).
    """
    def decorate(newfunc):
        name = func.__name__
        try:
            newfunc.__doc__ = func.__doc__
            newfunc.__module__ = func.__module__
            newfunc.__dict__ = func.__dict__
            newfunc.__name__ = name
        except TypeError:
            # can't set func name in 2.3
            newfunc.compat_func_name = name
        return newfunc
    return decorate

def raises(*exceptions):
    """Test must raise one of expected exceptions to pass. Example use::

      @raises(TypeError, ValueError)
      def test_raises_type_error():
          raise TypeError("This test passes")

      @raises(Exception):
      def test_that_fails_by_passing():
          pass
    """
    valid = ' or '.join([e.__name__ for e in exceptions])
    def decorate(func):
        name = func.__name__
        def newfunc(*arg, **kw):
            try:
                func(*arg, **kw)
            except exceptions:
                pass
            except:
                raise
            else:
                message = "%s() did not raise %s" % (name, valid)
                raise AssertionError(message)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate

def timed(limit):
    """Test must finish within specified time limit to pass. Example use::

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
    """Decorator to add setup and/or teardown methods to a test function

    @with_setup(setup, teardown)
    def test_something():
        # ...
    """
    def decorate(func, setup=setup, teardown=teardown):
        if setup:
            func.setup = setup
        if teardown:
            func.teardown = teardown
        return func
    return decorate
