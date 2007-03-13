import sys
import unittest
from inspect import ismethod
from nose.config import Config
from nose.context import FixtureContext
from nose.proxy import ResultProxyFactory, ResultProxy
from mock import RecordingPluginManager

class TestResultProxy(unittest.TestCase):

    def test_proxy_has_basic_methods(self):
        res = unittest.TestResult()
        proxy = ResultProxy(res, test=None)

        methods = [ 'addError', 'addFailure', 'addSuccess',
                    'startTest', 'stopTest', 'stop' ]
        for method in methods:
            m = getattr(proxy, method)
            assert ismethod(m), "%s is not a method" % method
            
    def test_proxy_has_nose_methods(self):
        res = unittest.TestResult()
        proxy = ResultProxy(res, test=None)

        methods = [ 'addSkip', 'addDeprecated', 'beforeTest', 'afterTest' ]
        for method in methods:
            m = getattr(proxy, method)
            assert ismethod(m), "%s is not a method" % method

    def test_proxy_proxies(self):
        class Dummy:
            def __init__(self):
                self.__dict__['called'] = []
            def __getattr__(self, attr):
                c = self.__dict__['called']
                c.append(attr)
                def dummy(*arg, **kw):
                    pass
                return dummy
        class TC(unittest.TestCase):
            def runTest(self):
                pass
        try:
            raise Exception("exception")
        except:
            err = sys.exc_info()
        context = FixtureContext()
        test = TC()
        case = context(test)
        res = Dummy()
        proxy = ResultProxy(res, test=case)
        proxy.addError(test, err)
        proxy.addFailure(test, err)
        proxy.addSuccess(test)
        proxy.addSkip(test, err)
        proxy.addDeprecated(test, err)
        proxy.startTest(test)
        proxy.stopTest(test)
        proxy.beforeTest(test)
        proxy.afterTest(test)
        proxy.stop()
        proxy.shouldStop = 'yes please'
        for method in ['addError', 'addFailure', 'addSuccess',
                       'addSkip', 'addDeprecated','startTest', 'stopTest',
                       'beforeTest', 'afterTest', 'stop']:
            assert method in res.called, "%s was not proxied"
        self.assertEqual(res.shouldStop, 'yes please')

    def test_proxy_handles_missing_methods(self):
        class TC(unittest.TestCase):
            def runTest(self):
                pass
        context = FixtureContext()
        test = TC()
        case = context(test)
        res = unittest.TestResult()
        proxy = ResultProxy(res, case)
        proxy.addSkip(test, None)
        proxy.addDeprecated(test, None)
        proxy.beforeTest(test)
        proxy.afterTest(test)
        
    def test_output_capture(self):
        res = unittest.TestResult()
        class TC(unittest.TestCase):
            def test_error(self):
                print "So long"
                raise TypeError("oops")
            def test_fail(self):
                print "Hello"
                self.fail()
        config = Config()
        config.capture = True
        context = FixtureContext(config=config)
        case = context(TC('test_fail'))

        case(res)
        assert res.failures
        self.assertEqual(case.captured_output, "Hello\n")

        res = unittest.TestResult()
        case = context(TC('test_error'))
        case(res)
        assert res.errors
        self.assertEqual(case.captured_output, "So long\n")

    def test_proxy_calls_plugins(self):
        from nose import SkipTest, DeprecatedTest
        res = unittest.TestResult()
        class TC(unittest.TestCase):
            def test_error(self):
                print "So long"
                raise TypeError("oops")
            def test_fail(self):
                print "Hello"
                self.fail()
            def test_skip(self):
                raise SkipTest('not it')
            def test_deprecated(self):
                raise DeprecatedTest('old n busted')
            def test(self):
                pass
        plugs = RecordingPluginManager()
        config = Config(plugins=plugs)
        context = FixtureContext(config=config)

        case_e = context(TC('test_error'))
        case_f = context(TC('test_fail'))
        case_s = context(TC('test_skip'))
        case_d = context(TC('test_deprecated'))
        case_t = context(TC('test'))

        case_e(res)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addError' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()
        
        case_f(res)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addFailure' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()

        case_s(res)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addSkip' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()

        case_d(res)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addDeprecated' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()

        case_t(res)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addSuccess' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()
            
if __name__ == '__main__':
    unittest.main()
