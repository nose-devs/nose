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
        self.suites = {}
        self.context = {}
        self.was_setup = {}
        self.was_torndown = {}

    def __call__(self, tests, parent=None):
        """Return (possibly creating a new) ContextSuite for parent,
        including tests.
        """
        suite = ContextSuite(
            tests, parent=parent, factory=self, config=self.config)
        self.suites.setdefault(parent, []).append(suite)
        self.context.setdefault(suite, []).append(parent)
        for ancestor in self.ancestry(parent):
            self.suites.setdefault(ancestor, []).append(suite)
            self.context[suite].append(ancestor)
        return suite
    
    def ancestry(self, parent):
        """Return the ancestry of the parent (that is, all of the
        packages and modules containing the parent), in order of
        descent with the outermost ancestor last. This method is a generator
        """
        log.debug("get ancestry %s", parent)
        if parent is None:
            return
        if hasattr(parent, '__module__'):
            ancestors = parent.__module__.split('.')
        elif hasattr(parent, '__name__'):
            ancestors = parent.__name__.split('.')[:-1]
        else:
            raise TypeError("%s has no ancestors?" % parent)
        while ancestors:
            log.debug(" %s ancestors %s", parent, ancestors)
            yield resolve_name('.'.join(ancestors))                
            ancestors.pop()
        

class ContextSuite(LazySuite):
    failureException = unittest.TestCase.failureException
    was_setup = False
    was_torndown = False
    
    def __init__(self, tests=(), parent=None, factory=None,
                 config=None, resultProxy=_def):
        log.debug("Context suite for %s (%s)", tests, parent)        
        self.parent = parent
        self.factory = factory
        if config is None:
            config = Config()
        self.config = config
        # Using a singleton to represent default instead of None allows
        # passing resultProxy=None to turn proxying off.
        if resultProxy is _def:
            resultProxy = ResultProxyFactory(config=config)
        self.resultProxy = resultProxy
        self.has_run = False
        LazySuite.__init__(self, tests)

    def __repr__(self):
        return "<%s parent=%s>" % (
            unittest._strclass(self.__class__), self.parent)
    __str__ = __repr__

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
            self.has_run = True
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.exc_info())

    def setUp(self):
        log.debug("suite setUp called, tests: %s", self._tests)
        if not self:
            # I have no tests
            return
        if self.was_setup:
            log.debug("Already set up")
            return
        parent = self.parent
        if parent is None:
            return
        # before running my own parent's setup, I need to
        # ask the factory if my parent's parents' setups have been run
        factory = self.factory
        if factory:
            # get a copy, since we'll be destroying it as we go
            ancestors = factory.context.get(self, [])[:]
            while ancestors:
                ancestor = ancestors.pop()
                log.debug("ancestor %s may need setup", ancestor)
                if ancestor in factory.was_setup:
                    continue
                log.debug("ancestor %s does need setup", ancestor)
                self.setupParent(ancestor)
            if parent in factory.was_setup:
                self.setupParent(parent)
        else:
            self.setupParent(parent)
        self.was_setup = True

    def setupParent(self, parent):
        # FIXME plugins.contextSetup(parent)
        log.debug("%s setup parent %s", self, parent)
        if self.factory:
            # note that I ran the setup for this parent, so that I'll run
            # the teardown in my teardown
            self.factory.was_setup[parent] = self
        if isclass(parent):
            names = ('setup_class',)
        else:
            names = ('setup_module', 'setup')
        # FIXME packages, camelCase
        try_run(parent, names)

    def tearDown(self):
        log.debug('context teardown')
        if not self.was_setup or self.was_torndown:
            log.debug(
                "No reason to teardown (was_setup? %s was_torndown? %s)"
                % (self.was_setup, self.was_torndown))
            return
        self.was_torndown = True
        parent = self.parent
        if parent is None:
            log.debug("No parent to tear down")
            return

        # for each ancestor... if the ancestor was setup
        # if I did the setup OR no other suites under that
        # ancestor exist that have not been run, I can do teardown
        factory = self.factory
        if factory:
            for ancestor in factory.context.get(self, []):
                log.debug('ancestor %s may need teardown', ancestor)
                if not ancestor in factory.was_setup:
                    log.debug('ancestor %s was not setup', ancestor)
                    continue
                if ancestor in factory.was_torndown:
                    log.debug('ancestor %s already torn down', ancestor)
                    continue
                setup = factory.was_setup[ancestor]
                if setup is self:
                    self.teardownParent(ancestor)
                else:
                    # I can still run teardown if all other suites
                    # in this context have run, and it's not yet
                    # torn down (supports loadTestsFromNames where
                    # N names are from the same/overlapping contexts)
                    suites = factory.suites[ancestor]
                    have_run = [ s for s in suites if s.has_run ]
                    if suites == have_run:
                        self.teardownParent(ancestor)
            if parent in factory.was_torndown:
                return
        self.teardownParent(parent)
        
    def teardownParent(self, parent):
        log.debug("%s teardown parent %s", self, parent)
        if isclass(parent):
            names = ('teardown_class',)
        else:
            names = ('teardown_module', 'teardown')
        # FIXME packages, camelCase
        try_run(parent, names)
        if self.factory:
            self.factory.was_torndown[parent] = self
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
