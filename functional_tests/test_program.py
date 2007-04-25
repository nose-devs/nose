import os
import unittest
from cStringIO import StringIO
from nose.core import TestProgram
from nose.config import Config

here = os.path.dirname(__file__)
support = os.path.join(here, 'support')

class TestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        self.result = unittest._TextTestResult(
            self.stream, self.descriptions, self.verbosity)
        return self.result 

class TestTestProgram(unittest.TestCase):

    def test_run_support_ctx(self):
        """Collect and run tests in functional_tests/support/ctx

        This should collect no tests in the default configuration, since
        none of the modules have test-like names.
        """
        stream = StringIO()
        runner = TestRunner(stream=stream)
        prog = TestProgram(defaultTest=os.path.join(support, 'ctx'),
                           argv=['test_run_support_ctx'],
                           testRunner=runner,
                           config=Config(exit=False))
        res = runner.result
        print stream.getvalue()
        self.assertEqual(res.testsRun, 0,
                         "Expected to run 0 tests, ran %s" % res.testsRun)
        assert res.wasSuccessful
        assert not res.errors
        assert not res.failures

    def test_run_support_package2(self):
        """Collect and run tests in functional_tests/support/package2

        This should collect and run 5 tests.
        """
        stream = StringIO()
        runner = TestRunner(stream=stream)

        prog = TestProgram(defaultTest=os.path.join(support, 'package2'),
                           argv=['test_run_support_package2', '-v'],
                           testRunner=runner,
                           config=Config(exit=False))
        res = runner.result
        print stream.getvalue()
        self.assertEqual(res.testsRun, 5,
                         "Expected to run 5 tests, ran %s" % res.testsRun)
        assert res.wasSuccessful
        assert not res.errors
        assert not res.failures
        
        

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
