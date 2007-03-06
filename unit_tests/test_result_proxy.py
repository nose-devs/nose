import unittest
from nose.config import Config
from nose.context import FixtureContext
from nose.proxy import ResultProxyFactory, ResultProxy


class TestResultProxy(unittest.TestCase):

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

        factory = ResultProxyFactory(config)
        context = FixtureContext(config=config, result_proxy=factory)
        case = context(TC('test_fail'))

        case(res)
        assert res.failures
        self.assertEqual(case.captured_output, "Hello\n")

        res = unittest.TestResult()
        case = context(TC('test_error'))
        case(res)
        assert res.errors
        self.assertEqual(case.captured_output, "So long\n")


if __name__ == '__main__':
    unittest.main()
