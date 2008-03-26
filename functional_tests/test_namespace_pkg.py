import os
import sys
import unittest
from cStringIO import StringIO
from nose.core import TestProgram
from test_program import TestRunner

here = os.path.dirname(__file__)
support = os.path.join(here, 'support')

class TestTestProgram(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.orig_path = sys.path[:]
        test_dir = os.path.join(support, 'namespace_pkg')
        os.chdir(test_dir)
        sys.path.append(os.path.join(test_dir, 'site-packages'))

    def tearDown(self):
        sys.path = self.orig_path
        os.chdir(self.cwd)

    def test_run_support_ctx(self):
        """Collect and run tests in functional_tests/support/ctx

        This should collect no tests in the default configuration, since
        none of the modules have test-like names.
        """
        stream = StringIO()
        runner = TestRunner(stream=stream)
        runner.verbosity = 2
        prog = TestProgram(argv=[''],
                           testRunner=runner,
                           exit=False)
        res = runner.result
        self.assertEqual(res.testsRun, 2,
                         "Expected to run 2 tests, ran %s" % res.testsRun)
        assert res.wasSuccessful()
        assert not res.errors
        assert not res.failures


if __name__ == '__main__':
    unittest.main()
