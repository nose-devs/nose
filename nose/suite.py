import logging
import sys
import unittest
from nose.config import Config

log = logging.getLogger(__name__)

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

        

#
# FIXME how to get the result proxy in there? Does it make sense
# to put that into the context?
#

class ContextSuiteFactory(object):
    def __init__(self, context, config=None):
        self.context = context
        if config is None:
            config = Config()
        self.config = config

    def __call__(self, tests, parent=None):
        context = self.context(parent, config=self.config)
        return ContextSuite(tests, context)


class ContextSuite(LazySuite):
    failureException = unittest.TestCase.failureException
    was_setup = False
    
    def __init__(self, tests=(), context=None):        
        if context:
            self.context = context
        LazySuite.__init__(self, tests)

    def _add_context(self, test):
        if hasattr(test, 'context'):
            return test
        return self.context(test)

    def exc_info(self):
        """Hook for replacing error tuple output
        """
        return sys.exc_info()

    def run(self, result):
        """Run tests in suite inside of suite fixtures.
        """
        # FIXME proxy the result *here*
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
                # FIXME and proxy the result *here*
                test(result)
        finally:
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.exc_info())

    def setUp(self):
        log.debug("suite setUp called, tests: %s", self._tests)
        if self:
            self.context.setup()
            self.was_setup = True

    def tearDown(self):
        if self.was_setup:
            self.context.teardown()
        
    def _get_tests_with_context(self):
        for test in self._get_tests():
            if hasattr(test, 'context'):
                yield test
            else:
                yield self.context(test)

    _tests = property(_get_tests_with_context, LazySuite._set_tests, None,
                      "Access the tests in this suite. Tests are returned "
                      "inside of a context wrapper.")
