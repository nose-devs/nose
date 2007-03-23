import logging
import sys
import unittest
from inspect import isclass
from nose.case import Test
from nose.config import Config
from nose.proxy import ResultProxyFactory
from nose.util import resolve_name, try_run

log = logging.getLogger(__name__)

# Singleton for default value -- see ContextSuite.__init__ below
_def = object()


class LazySuite(unittest.TestSuite):

    def __init__(self, tests=()):
        self._set_tests(tests)
                

    def __repr__(self):
        return "<%s tests=generator (%s)>" % (
            unittest._strclass(self.__class__), id(self))
    
    __str__ = __repr__

    def addTest(self, test):
        log.debug("Adding precached test %s", test)
        self._precache.append(test)

    def __nonzero__(self):
        if self._precache:
            return True
        if self.test_generator is None:
            return False
        try:
            test = self.test_generator.next()
            if test is not None:
                self._precache.append(test)
                return True
        except StopIteration:
            pass
        return False

    def _get_tests(self):
        log.debug("precache is %s", self._precache)
        for test in self._precache:
            yield test
        if self.test_generator is None:
            return
        for test in self.test_generator:
            yield test

    def _set_tests(self, tests):
        self._precache = []
        is_suite = isinstance(tests, unittest.TestSuite)
        if callable(tests) and not is_suite:
            log.debug("tests is callable and not a test suite")
            self.test_generator = tests()
        elif is_suite:
            # Suites need special treatment: they must be called like
            # tests for their setup/teardown to run (if any)
            self.addTests([tests])
            self.test_generator = None
        else:
            log.debug("tests is not callable, spooling it out")
            self.addTests(tests)
            self.test_generator = None

    _tests = property(_get_tests, _set_tests, None,
                      "Access the tests in this suite. Access is through a "
                      "generator, so iteration may not be repeatable.")

        

class ContextSuiteFactory(object):
    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.config = config
        self.suites = []

    def __call__(self, tests, parent=None):
        """Return (possibly creating a new) ContextSuite for parent,
        including tests.

        
        


        """
        # The easy case: there are no other suites to worry about
        # so our only concern is that we roll up the parent tree to find
        # all of the ancestors of the parent and produce a hierarchy
        # of suites so that all parents get their fixtures called
        if not self.suites:
            suite = ContextSuite(tests, parent, config=self.config)
            self.suites.append(suite)
            for ancestor in self.ancestry(parent):
                suite = ContextSuite(suite, ancestor, config=self.config)
                self.suites.append(suite)
            return suite

    def ancestry(self, parent):
        """Return the ancestry of the parent (that is, all of the
        packages and modules containing the parent), in order of
        descent with the outermost ancestor last. This method is a generator
        """
        if hasattr(parent, '__module__'):
            ancestors = parent.__module__.split('.')
        elif hasattr(parent, '__name__'):
            ancestors = parent.__name__.split('.')[:-1]
        while ancestors:
            print ancestors
            yield resolve_name('.'.join(ancestors))                
            ancestors.pop()
            
        

class ContextSuite(LazySuite):
    failureException = unittest.TestCase.failureException
    was_setup = False
    was_torndown = False
    
    def __init__(self, tests=(), parent=None, config=None, resultProxy=_def):
        log.debug("Context suite for %s (%s)", tests, parent)
        self.parent = parent
        if config is None:
            config = Config()
        # Using a singleton to represent default instead of None allows
        # passing resultProxy=None to turn proxying off.
        if resultProxy is _def:
            resultProxy = ResultProxyFactory(config=config)
        self.config = config
        self.resultProxy = resultProxy
        LazySuite.__init__(self, tests)

    def exc_info(self):
        """Hook for replacing error tuple output
        """
        return sys.exc_info()

    def run(self, result):
        """Run tests in suite inside of suite fixtures.
        """
        # proxy the result for myself
        config = self.config
        if self.resultProxy:
            result, orig = self.resultProxy(result, self), result
        else:
            result, orig = result, result
        try:
            self.setUp()
        except KeyboardInterrupt:
            raise
        except:
            result.addError(self, self.exc_info())
            return
        try:
            for test in self._tests:
                log.debug("running test %s", test)
                if result.shouldStop:
                    break
                # each nose.case.Test will create its own result proxy
                # so the cases need the original result, to avoid proxy
                # chains
                test(orig)
        finally:
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.exc_info())

    def setUp(self):
        log.debug("suite setUp called, tests: %s", self._tests)
        if not self or self.was_setup:
            return
        parent = self.parent
        if parent is None:
            return
        # FIXME plugins.contextSetup(parent)
        if isclass(parent):
            names = ('setup_class',)
        else:
            names = ('setup_module', 'setup')
        # FIXME packages, camelCase
        try_run(parent, names)
        self.was_setup = True

    def tearDown(self):
        log.debug('context teardown')
        if not self.was_setup or self.was_torndown:
            return
        parent = self.parent
        if parent is None:
            return
        if isclass(parent):
            names = ('teardown_class',)
        else:
            names = ('teardown_module', 'teardown')
        # FIXME packages, camelCase
        try_run(parent, names)
        self.was_torndown = True
        # FIXME plugins.contextTeardown(parent)
        
    def _get_wrapped_tests(self):
        for test in self._get_tests():
            if isinstance(test, Test) or isinstance(test, unittest.TestSuite):
                yield test
            else:
                yield Test(test,
                           config=self.config,
                           resultProxy=self.resultProxy)

    _tests = property(_get_wrapped_tests, LazySuite._set_tests, None,
                      "Access the tests in this suite. Tests are returned "
                      "inside of a context wrapper.")
