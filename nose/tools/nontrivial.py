"""Tools not exempt from being descended into in tracebacks"""

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


def raises(*exceptions):
    """Test must raise one of expected exceptions to pass.

    Example use::

      @raises(TypeError, ValueError)
      def test_raises_type_error():
          raise TypeError("This test passes")

      @raises(Exception)
      def test_that_fails_by_passing():
          pass

    If you want to test many assertions about exceptions in a single test,
    you may want to use `assert_raises` instead.
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
            result = func(*arg, **kw)
            end = time.time()
            if end - start > limit:
                raise TimeExpired("Time limit (%s) exceeded" % limit)
            return result
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate


def _smart_run(func, args, kwargs):
    """Given a function definition, determine which of the args and
    kwargs are relevant and then execute the function"""
    fc = func.func_code
    kwargs2 = dict(
        (k, kwargs[k])
        for k in kwargs if k in fc.co_varnames[:fc.co_nlocals])
    args2 = args[:fc.co_nlocals - len(kwargs2)]
    func(*args2, **kwargs2)


def with_setup(setup=None, teardown=None, params=False):
    """Decorator to add setup and/or teardown methods to a test function::

      @with_setup(setup, teardown)
      def test_something():
          " ... "

    Note that `with_setup` is useful *only* for test functions, not for test
    methods or inside of TestCase subclasses.
    """
    def decorate(func, setup=setup, teardown=teardown):
        args = []
        kwargs = {}
        if params:
            @make_decorator(func)
            def func_wrapped():
                _smart_run(func, args, kwargs)
        else:
            func_wrapped = func
        if setup:
            def setup_wrapped():
                rv = setup()
                if rv is not None:
                    args.extend(rv[0])
                    kwargs.update(rv[1])

            if hasattr(func, 'setup'):
                _old_s = func.setup

                def _s():
                    setup_wrapped()
                    _old_s()
                func_wrapped.setup = _s
            else:
                if params:
                    func_wrapped.setup = setup_wrapped
                else:
                    func_wrapped.setup = setup

        if teardown:
            if hasattr(func, 'teardown'):
                _old_t = func.teardown

                def _t():
                    _old_t()
                    _smart_run(teardown, args, kwargs)
                func_wrapped.teardown = _t
            else:
                if params:
                    func_wrapped.teardown = lambda: _smart_run(
                        teardown, args, kwargs)
                else:
                    func_wrapped.teardown = teardown
        return func_wrapped
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
