"""Compatibility shim for running under the setuptools test command. The
ResultProxy wraps the actual TestResult passed to a test and implements output
capture and plugin support. TestProxy wraps test cases and in those wrapped
test cases, wraps the TestResult with a ResultProxy.

To enable this functionality, use ResultProxySuite as the suiteClass in a
TestLoader.
"""
import logging
import unittest
from nose.result import Result, ln

log = logging.getLogger(__name__)

class ResultProxy(Result):
    """Result proxy. Performs nose-specific result operations, such as
    handling output capture, inspecting assertions and calling plugins,
    then delegates to another result handler.
    """
    def __init__(self, result):
        self.result = result
    
    def addError(self, test, err):
        log.debug('Proxy addError %s %s', test, err)
        Result.addError(self, test, err)
        
        # compose a new error object that includes captured output
        if self.capt is not None and len(self.capt):
            ec, ev, tb = err
            ev = '\n'.join([str(ev) , ln('>> begin captured stdout <<'),
                            self.capt, ln('>> end captured stdout <<')])
            err = (ec, ev, tb)
        self.result.addError(test, err)
        
    def addFailure(self, test, err):
        log.debug('Proxy addFailure %s %s', test, err)
        Result.addFailure(self, test, err)
        
        # compose a new error object that includes captured output
        # and assert introspection data
        ec, ev, tb = err
        if self.tbinfo is not None and len(self.tbinfo):
            ev = '\n'.join([str(ev), self.tbinfo])
        if self.capt is not None and len(self.capt):
            ev = '\n'.join([str(ev) , ln('>> begin captured stdout <<'),
                            self.capt, ln('>> end captured stdout <<')])
        err = (ec, ev, tb)        
        self.result.addFailure(test, err)
        
    def addSuccess(self, test):
        Result.addSuccess(self, test)
        self.result.addSuccess(test)
    
    def startTest(self, test):
        Result.startTest(self, test)
        self.result.startTest(test)

    def stopTest(self, test):
        Result.stopTest(self, test)
        self.result.stopTest(test)

    def _get_shouldStop(self):
        return self.result.shouldStop

    def _set_shouldStop(self, val):
        self.result.shouldStop = val
        
    shouldStop = property(_get_shouldStop, _set_shouldStop)

    
class ResultProxySuite(unittest.TestSuite):
    """Test suite that supports output capture, etc, by wrapping each test in
    a TestProxy.
    """

    def __iter__(self):
        # Needed for 2.3 compatibility
        return iter(self._tests)
    
    def addTest(self, test):
        """Add test, first wrapping in TestProxy"""
        self._tests.append(TestProxy(test))

        
class TestProxy(unittest.TestCase):
    """Test case that wraps the test result in a ResultProxy.
    """
    resultProxy = ResultProxy
    
    def __init__(self, wrapped_test):
        self.wrapped_test = wrapped_test
        log.debug('%r.__init__', self)
        
    def __call__(self, *arg, **kw):
        log.debug('%r.__call__', self)
        self.run(*arg, **kw)

    def __repr__(self):
        return "TestProxy for: %r" % self.wrapped_test
        
    def __str__(self):
        return str(self.wrapped_test)    

    def id(self):
        return self.wrapped_test.id()
        
    def run(self, result):
        log.debug('TestProxy run test %s in proxy %s for result %s',
                  self, self.resultProxy, result)
        self.wrapped_test(self.resultProxy(result))

    def shortDescription(self):
        return self.wrapped_test.shortDescription()
