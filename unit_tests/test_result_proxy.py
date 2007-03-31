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

        methods = [ 'beforeTest', 'afterTest' ]
        for method in methods:
            m = getattr(proxy, method)
            assert ismethod(m), "%s is not a method" % method

    def test_proxy_proxies(self):
        from nose.case import Test
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
        test = TC()
        case = Test(test)
        res = Dummy()
        proxy = ResultProxy(res, test=case)
        proxy.addError(test, err)
        proxy.addFailure(test, err)
        proxy.addSuccess(test)
        proxy.startTest(test)
        proxy.stopTest(test)
        proxy.beforeTest(test)
        proxy.afterTest(test)
        proxy.stop()
        proxy.shouldStop = 'yes please'
        for method in ['addError', 'addFailure', 'addSuccess',
                       'startTest', 'stopTest', 'beforeTest', 'afterTest',
                       'stop']:
            assert method in res.called, "%s was not proxied"
        self.assertEqual(res.shouldStop, 'yes please')

    def test_proxy_handles_missing_methods(self):
        from nose.case import Test
        class TC(unittest.TestCase):
            def runTest(self):
                pass
        test = TC()
        case = Test(test)
        res = unittest.TestResult()
        proxy = ResultProxy(res, case)
        proxy.beforeTest(test)
        proxy.afterTest(test)
        
    def test_proxy_calls_plugins(self):
        from nose.case import Test
        res = unittest.TestResult()
        class TC(unittest.TestCase):
            def test_error(self):
                print "So long"
                raise TypeError("oops")
            def test_fail(self):
                print "Hello"
                self.fail()
            def test(self):
                pass
        plugs = RecordingPluginManager()
        config = Config(plugins=plugs)

        factory = ResultProxyFactory(config=config)

        case_e = Test(TC('test_error'))
        case_f = Test(TC('test_fail'))
        case_t = Test(TC('test'))

        pres_e = factory(res, case_e)
        case_e(pres_e)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addError' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()

        pres_f = factory(res, case_f)
        case_f(pres_f)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addFailure' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()

        pres_t = factory(res, case_t)
        case_t(pres_t)
        assert 'beforeTest' in plugs.called
        assert 'startTest' in plugs.called
        assert 'addSuccess' in plugs.called
        assert 'stopTest' in plugs.called
        assert 'afterTest' in plugs.called
        plugs.reset()
            
if __name__ == '__main__':
    unittest.main()
