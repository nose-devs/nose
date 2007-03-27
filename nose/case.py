"""nose unittest.TestCase subclasses. It is not necessary to subclass these
classes when writing tests; they are used internally by nose.loader.TestLoader
to create test cases from test functions and methods in test classes.
"""
import logging
import sys
import unittest
from traceback import format_tb
from nose.config import Config
from nose.util import try_run

log = logging.getLogger(__name__)


# FIXME probably not the best name, since it is mainly used for errors
class Failure(unittest.TestCase):
    def __init__(self, exc_class, exc_val, tb=None):
        log.debug("A failure! %s %s %s", exc_class, exc_val, format_tb(tb))
        self.exc_class = exc_class
        self.exc_val = exc_val
        self.tb = tb
        unittest.TestCase.__init__(self)

    def __str__(self):
        return "Failure: %s(%s)" % (self.exc_class, self.exc_val)

    def runTest(self):
        if self.tb is not None:
            raise self.exc_class, self.exc_val, self.tb
        else:
            raise self.exc_class(self.exc_val)


class Test(unittest.TestCase):
    """The universal test case wrapper.

    When a plugin sees a test, it will always see an instance of this
    class. To access the actual test case that will be run, access the
    test property of the nose.case.Test instance.    
    """
    def __init__(self, test, config=None, resultProxy=None):
        log.debug("Test(%s)", test)
        # sanity check
        if not callable(test):
            raise TypeError("nose.case.Test called with argument %r that "
                            "is not callable. A callable is required."
                            % test)
        self.test = test
        if config is None:
            config = Config()
        self.config = config
        self.assertDetails = None
        self.capturedOutput = None
        self.resultProxy = resultProxy
        unittest.TestCase.__init__(self)
        
    def __call__(self, *arg, **kwarg):
        log.debug("Test call %s %s %s", self, arg, kwarg)
        return self.run(*arg, **kwarg)

    def __str__(self):
        # FIXME plugins.testName(self)
        return str(self.test)

    def __repr__(self):
        return "Test(%r)" % self.test

    def afterTest(self, result):
        log.debug("Test afterTest %s", self)
        try:
            result.afterTest(self.test)
        except AttributeError:
            pass

    def beforeTest(self, result):
        log.debug("Test beforeTest %s", self)
        try:
            result.beforeTest(self.test)
        except AttributeError:
            pass

    def exc_info(self):
        """Extract exception info into a useable form, including
        appending captured output and assert introspection information, if
        so configured.
        """
        # FIXME add in the stdout capture and such
        exc, exv, tb = sys.exc_info()
        return (exc, exv, tb)
        
    def id(self):
        return self.test.id()

    def run(self, result):
        """Modified run for the test wrapper.

        From here we don't call result.startTest or stopTest or
        addSuccess.  The wrapper calls addError/addFailure only if its
        own setup or teardown fails, or running the wrapped test fails
        (eg, if the wrapped "test" is not callable).

        Two additional methods are called, beforeTest and
        afterTest. These give plugins a chance to modify the wrapped
        test before it is called and do cleanup after it is
        called. They are called unconditionally.
        """
        if self.resultProxy:
            result = self.resultProxy(result, self)
        self.beforeTest(result)
        try:
            try:
                self.runTest(result)
            except KeyboardInterrupt:
                raise
            except:
                err = sys.exc_info()
                result.addError(self, err)
        finally:
            self.afterTest(result)
        
    def runTest(self, result):
        log.debug('run test %s with result %s', self.test, result)
        self.test(result)
        
    def shortDescription(self):
        # FIXME plugins.describeTest(self)
        return self.test.shortDescription()
        

class TestBase(unittest.TestCase):
    """Common functionality for FunctionTestCase and MethodTestCase.
    """
    def id(self):
        return str(self)
        
    def runTest(self):
        log.debug("%s.runTest(%s)", self.__class__.__name__, self)
        self.test(*self.arg)
    
    def shortDescription(self):
        func, arg = self._descriptors()
        doc = getattr(func, '__doc__', None)
        if not doc:
            doc = str(self)
        return doc.split("\n")[0].strip()

    
class FunctionTestCase(TestBase):
    """TestCase wrapper for test functions.

    Don't use this class directly; it is used internally in nose to
    create test cases for test functions.
    
    This class is very similar to unittest.FunctionTestCase, with a few
    extensions:
      * The test descriptions are disambiguated by including the full
        module path when a test with a similar name has been seen in
        the test run. 
      * It allows setup and teardown functions to be defined as attributes
        of the test function. A convenient way to set this up is via the
        provided with_setup decorator:

        def setup_func():
            # ...

        def teardown_func():
            # ...
        
        @with_setup(setup_func, teardown_func)        
        def test_something():
            # ...

    """
    
    def __init__(self, test, setUp=None, tearDown=None, arg=tuple(),
                 descriptor=None):
        self.test = test
        self.setUpFunc = setUp
        self.tearDownFunc = tearDown
        self.arg = arg
        self.descriptor = descriptor
        unittest.TestCase.__init__(self)
        
    def setUp(self):
        """Run any setup function attached to the test function
        """
        if self.setUpFunc:
            self.setUpFunc()
        else:
            names = ('setup', 'setUp', 'setUpFunc')
            try_run(self.test, names)

    def tearDown(self):
        """Run any teardown function attached to the test function
        """
        if self.tearDownFunc:
            self.tearDownFunc()
        else:
            names = ('teardown', 'tearDown', 'tearDownFunc')
            try_run(self.test, names)
        
    def __str__(self):
        func, arg = self._descriptors()
        if hasattr(func, 'compat_func_name'):
            name = func.compat_func_name
        else:
            name = func.__name__
        name = "%s.%s" % (func.__module__, name)
        if arg:
            name = "%s%s" % (name, arg)
        # FIXME need to include the full dir path to disambiguate
        # in cases where test module of the same name was seen in
        # another directory (old fromDirectory)
        return name 
    __repr__ = __str__
    
    def _descriptors(self):
        """Get the descriptors of the test function: the function and
        arguments that will be used to construct the test name. In
        most cases, this is the function itself and no arguments. For
        tests generated by generator functions, the original
        (generator) function and args passed to the generated function
        are returned.
        """
        if self.descriptor:
            return self.descriptor, self.arg
        else:            
            return self.test, self.arg


class MethodTestCase(TestBase):
    """Test case wrapper for test methods.

    Don't use this class directly; it is used internally in nose to
    create test cases for test methods.
    """
    def __init__(self, method, test=None, arg=tuple(), descriptor=None):
        """Initialize the MethodTestCase.

        Required argument:

        * method -- the method to call, may be bound or unbound. In either
        case, a new instance of the method's class will be instantiated to
        make the call.

        Optional arguments:

        * test -- the test function to call. If this is passed, it will be
          called instead of getting a new bound method of the same name as the
          desired method from the test instance. This is to support generator
          methods that yield inline functions.

        * arg -- arguments to pass to the test function. This is to support
          generator methods that yield arguments.

        * descriptor -- the function, other than the test, that should be used
          to construct the test name. This is to support generator methods.
        """
        log.debug("MethodTestCase for %s", method)
        self.method = method
        self.test = test
        self.arg = arg
        self.descriptor = descriptor
        self.cls = method.im_class
        self.inst = self.cls()
        if self.test is None:
            method_name = self.method.__name__
            self.test = getattr(self.inst, method_name)            
        unittest.TestCase.__init__(self)

    def __str__(self):
        func, arg = self._descriptors()
        if hasattr(func, 'compat_func_name'):
            name = func.compat_func_name
        else:
            name = func.__name__
        name = "%s.%s.%s" % (func.__module__,
                             self.cls.__name__,
                             name)
        if arg:
            name = "%s%s" % (name, arg)
        return name
    __repr__ = __str__

    def setUp(self):
        log.debug("MethodTestCase.setUp(%s)", self)
        try_run(self.inst, ('setup', 'setUp'))

    def tearDown(self):
        log.debug("MethodTestCase.tearDown(%s)", self)
        try_run(self.inst, ('teardown', 'tearDown'))
        
    def _descriptors(self):
        """Get the descriptors of the test method: the method and
        arguments that will be used to construct the test name. In
        most cases, this is the method itself and no arguments. For
        tests generated by generator methods, the original
        (generator) method and args passed to the generated method 
        or function are returned.
        """
        if self.descriptor:
            return self.descriptor, self.arg
        else:
            return self.method, self.arg
        
        
