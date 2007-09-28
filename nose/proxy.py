"""
Result Proxy
------------

The result proxy wraps the result instance given to each test. It
performs two functions: enabling extended error/failure reporting
and calling plugins.

As each result event is fired, plugins are called with the same event;
however, plugins are called with the nose.case.Test instance that
wraps the actual test. So when a test fails and calls
result.addFailure(self, err), the result proxy calls
addFailure(self.test, err) for each plugin. This allows plugins to
have a single stable interface for all test types, and also to
manipulate the test object itself by setting the `test` attribute of
the nose.case.Test that they receive.
"""
import logging
from nose.config import Config


log = logging.getLogger(__name__)

class ResultProxyFactory(object):
    """Factory for result proxies. Generates a ResultProxy bound to each test
    and the result passed to the test.
    """
    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.config = config
        self.__prepared = False
        self.__result = None

    def __call__(self, result, test):
        """Return a ResultProxy for the current test.

        On first call, plugins are given a chance to replace the
        result used for the remaining tests. If a plugin returns a
        value from prepareTestResult, that object will be used as the
        result for all tests.
        """
        if not self.__prepared:
            self.__prepared = True
            plug_result = self.config.plugins.prepareTestResult(result)
            if plug_result is not None:
                self.__result = result = plug_result
        if self.__result is not None:
            result = self.__result
        return ResultProxy(result, test, config=self.config)


class ResultProxy(object):
    """Proxy to TestResults (or other results handler).

    One ResultProxy is created for each nose.case.Test. The result proxy
    calls plugins with the nose.case.Test instance (instead of the
    wrapped test case) as each result call is made. Finally, the real result
    method is called with the wrapped test.
    """    
    def __init__(self, result, test, config=None):
        if config is None:
            config = Config()
        self.config = config
        self.plugins = config.plugins
        self.result = result
        self.test = test

    def __repr__(self):
        return repr(self.result)

    def assertMyTest(self, test):
        # The test I was called with must be my .test or my
        # .test's .test. or my .test.test's .case

        case = getattr(self.test, 'test', None)
        assert (test is self.test 
                or test is case 
                or test is getattr(case, '_nose_case', None), 
                "ResultProxy for %r (%s) was called with test %r (%s)" 
                % (self.test, id(self.test), test, id(test)))
    
    def afterTest(self, test):
        self.assertMyTest(test)
        self.plugins.afterTest(self.test)
        try:
            self.result.afterTest(self.test)
        except AttributeError:
            pass

    def beforeTest(self, test):
        self.assertMyTest(test)
        self.plugins.beforeTest(self.test)
        try:
            self.result.beforeTest(self.test)
        except AttributeError:
            pass
        
    def addError(self, test, err):
        self.assertMyTest(test)
        plugins = self.plugins
        plugin_handled = plugins.handleError(self.test, err)
        if plugin_handled:
            return
        formatted = plugins.formatError(self.test, err)
        if formatted is not None:
            err = formatted
        plugins.addError(self.test, err)
        self.result.addError(self.test, err)
        if self.config.stopOnError:
            self.shouldStop = True

    def addFailure(self, test, err):
        self.assertMyTest(test)
        plugins = self.plugins
        plugin_handled = plugins.handleFailure(self.test, err)
        if plugin_handled:
            return
        formatted = plugins.formatFailure(self.test, err)
        if formatted is not None:
            err = formatted
        plugins.addFailure(self.test, err)
        self.result.addFailure(self.test, err)
        if self.config.stopOnError:
            self.shouldStop = True
    
    def addSuccess(self, test):
        self.assertMyTest(test)
        self.plugins.addSuccess(self.test)
        self.result.addSuccess(self.test)

    def startTest(self, test):
        self.assertMyTest(test)
        self.plugins.startTest(self.test)
        self.result.startTest(self.test)
    
    def stop(self):
        self.result.stop()
    
    def stopTest(self, test):
        self.assertMyTest(test)
        self.plugins.stopTest(self.test)
        self.result.stopTest(self.test)
    
    def get_shouldStop(self):
        return self.result.shouldStop

    def set_shouldStop(self, shouldStop):
        self.result.shouldStop = shouldStop

    shouldStop = property(get_shouldStop, set_shouldStop, None,
                          """Should the test run stop?""")
