import os
import sys
import unittest
from difflib import ndiff
from nose import loader
from nose import suite

support = os.path.abspath(os.path.join(os.path.dirname(__file__), 'support'))

class TestNoseTestLoader(unittest.TestCase):

    def setUp(self):
        self._mods = sys.modules.copy()
        # suite.ContextSuiteFactory.suiteClass = suite.TreePrintContextSuite

    def tearDown(self):
        to_del = [ m for m in sys.modules.keys() if
                   m not in self._mods ]
        if to_del:
            for mod in to_del:
                del sys.modules[mod]
        sys.modules.update(self._mods)
        # suite.ContextSuiteFactory.suiteClass = suite.ContextSuite

    def test_load_from_name_file(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package1')
        l = loader.TestLoader(workingDir=wd)

        file_suite = l.loadTestsFromName('tests/test_example_function.py')
        file_suite(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

    def test_load_from_name_dot(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package1')
        l = loader.TestLoader(workingDir=wd)
        dir_suite = l.loadTestsFromName('.')
        dir_suite(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

    def test_fixture_context(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(workingDir=wd)
        dir_suite = l.loadTestsFromName('.')
        dir_suite(res)

        m = sys.modules['test_pak']
        print "test pak state", m.state

        assert not res.errors, res.errors
        assert not res.failures, res.failures
        self.assertEqual(res.testsRun, 5)

        # Expected order of calls
        expect = ['test_pak.setup',
                  'test_pak.test_mod.setup',
                  'test_pak.test_mod.test_add',
                  'test_pak.test_mod.test_minus',
                  'test_pak.test_mod.teardown',
                  'test_pak.test_sub.setup',
                  'test_pak.test_sub.test_mod.setup',
                  'test_pak.test_sub.test_mod.TestMaths.setup_class',
                  'test_pak.test_sub.test_mod.TestMaths.setup',
                  'test_pak.test_sub.test_mod.TestMaths.test_div',
                  'test_pak.test_sub.test_mod.TestMaths.teardown',
                  'test_pak.test_sub.test_mod.TestMaths.setup',
                  'test_pak.test_sub.test_mod.TestMaths.test_two_two',
                  'test_pak.test_sub.test_mod.TestMaths.teardown',
                  'test_pak.test_sub.test_mod.TestMaths.teardown_class',
                  'test_pak.test_sub.test_mod.test',
                  'test_pak.test_sub.test_mod.teardown',
                  'test_pak.test_sub.teardown',
                  'test_pak.teardown']
        self.assertEqual(len(m.state), len(expect))
        for item in m.state:
            self.assertEqual(item, expect.pop(0))

    def test_fixture_context_name_is_module(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(workingDir=wd)
        suite = l.loadTestsFromName('test_pak.test_mod')
        suite(res)

        assert 'test_pak' in sys.modules, \
               "Context did not load test_pak"
        m = sys.modules['test_pak']
        print "test pak state", m.state
        expect = ['test_pak.setup',
                  'test_pak.test_mod.setup',
                  'test_pak.test_mod.test_add',
                  'test_pak.test_mod.test_minus',
                  'test_pak.test_mod.teardown',
                  'test_pak.teardown']
        self.assertEqual(len(m.state), len(expect))
        for item in m.state:
            self.assertEqual(item, expect.pop(0))

    def test_fixture_context_name_is_test_function(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(workingDir=wd)
        suite = l.loadTestsFromName('test_pak.test_mod:test_add')
        suite(res)

        assert 'test_pak' in sys.modules, \
               "Context did not load test_pak"
        m = sys.modules['test_pak']
        print "test pak state", m.state
        expect = ['test_pak.setup',
                  'test_pak.test_mod.setup',
                  'test_pak.test_mod.test_add',
                  'test_pak.test_mod.teardown',
                  'test_pak.teardown']
        self.assertEqual(len(m.state), len(expect))
        for item in m.state:
            self.assertEqual(item, expect.pop(0))

    def test_fixture_context_name_is_test_class(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(workingDir=wd)
        suite = l.loadTestsFromName(
            'test_pak.test_sub.test_mod:TestMaths')
        suite(res)

        assert 'test_pak' in sys.modules, \
               "Context did not load test_pak"
        m = sys.modules['test_pak']
        # print "test pak state", m.state
        expect = ['test_pak.setup',
                  'test_pak.test_sub.setup',
                  'test_pak.test_sub.test_mod.setup',
                  'test_pak.test_sub.test_mod.TestMaths.setup_class',
                  'test_pak.test_sub.test_mod.TestMaths.setup',
                  'test_pak.test_sub.test_mod.TestMaths.test_div',
                  'test_pak.test_sub.test_mod.TestMaths.teardown',
                  'test_pak.test_sub.test_mod.TestMaths.setup',
                  'test_pak.test_sub.test_mod.TestMaths.test_two_two',
                  'test_pak.test_sub.test_mod.TestMaths.teardown',
                  'test_pak.test_sub.test_mod.TestMaths.teardown_class',
                  'test_pak.test_sub.test_mod.teardown',
                  'test_pak.test_sub.teardown',
                  'test_pak.teardown']
        self.assertEqual(m.state, expect, diff(expect, m.state))

    def test_fixture_context_name_is_test_class_test(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(workingDir=wd)
        suite = l.loadTestsFromName(
            'test_pak.test_sub.test_mod:TestMaths.test_div')
        suite(res)

        assert 'test_pak' in sys.modules, \
               "Context not load test_pak"
        m = sys.modules['test_pak']
        print "test pak state", m.state
        expect = ['test_pak.setup',
                  'test_pak.test_sub.setup',
                  'test_pak.test_sub.test_mod.setup',
                  'test_pak.test_sub.test_mod.TestMaths.setup_class',
                  'test_pak.test_sub.test_mod.TestMaths.setup',
                  'test_pak.test_sub.test_mod.TestMaths.test_div',
                  'test_pak.test_sub.test_mod.TestMaths.teardown',
                  'test_pak.test_sub.test_mod.TestMaths.teardown_class',
                  'test_pak.test_sub.test_mod.teardown',
                  'test_pak.test_sub.teardown',
                  'test_pak.teardown']
        self.assertEqual(m.state, expect, diff(expect, m.state))

    def test_mod_setup_fails_no_tests_run(self):
        ctx = os.path.join(support, 'ctx')
        l = loader.TestLoader(workingDir=ctx)
        suite = l.loadTestsFromName('mod_setup_fails.py')

        res = unittest.TestResult()
        suite(res)

        assert res.errors
        assert not res.failures, res.failures
        assert res.testsRun == 0, \
               "Expected to run 0 tests but ran %s" % res.testsRun

    def test_mod_setup_skip_no_tests_run_no_errors(self):
        # FIXME need to load a config with builtin plugins
        ctx = os.path.join(support, 'ctx')
        l = loader.TestLoader(workingDir=ctx)
        suite = l.loadTestsFromName('mod_setup_skip.py')

        res = unittest.TestResult()
        suite(res)

        assert not suite.was_setup, "Suite setup did not fail"
        assert not res.errors, res.errors
        assert not res.failures, res.failures
        assert res.testsRun == 0, \
               "Expected to run 0 tests but ran %s" % res.testsRun

    def test_mod_import_skip_one_test_no_errors(self):
        # FIXME need to load a config with builtin plugins
        ctx = os.path.join(support, 'ctx')
        l = loader.TestLoader(workingDir=ctx)
        suite = l.loadTestsFromName('mod_import_skip.py')

        res = unittest.TestResult()
        suite(res)

        assert not res.errors, res.errors
        assert not res.failures, res.failures
        assert res.testsRun == 1, \
               "Expected to run 1 tests but ran %s" % res.testsRun

    def test_failed_import(self):
        ctx = os.path.join(support, 'ctx')
        l = loader.TestLoader(workingDir=ctx)
        suite = l.loadTestsFromName('no_such_module.py')

        res = unittest._TextTestResult(
            stream=unittest._WritelnDecorator(sys.stdout),
            descriptions=0, verbosity=1)
        suite(res)

        print res.errors
        res.printErrors()
        assert res.errors, "Expected errors but got none"
        assert not res.failures, res.failures
        assert res.testsRun == 1, \
               "Expected to run 1 tests but ran %s" % res.testsRun

# used for comparing lists
def diff(a, b):
    return '\n' + '\n'.join([ l for l in ndiff(a, b)
                              if not l.startswith('  ') ])


# used for context debugging
class TreePrintContextSuite(suite.ContextSuite):
    indent = ''

    def setUp(self):
        print self, 'setup -->'
        ContextSuite.setUp(self)
        TreePrintContextSuite.indent += '  '

    def tearDown(self):
        TreePrintContextSuite.indent = TreePrintContextSuite.indent[:-2]
        try:
            ContextSuite.tearDown(self)
        finally:
            print self, 'teardown <--'
    def __repr__(self):
        return '%s[%s]' % (self.indent, self.parent.__name__)
    __str__ = __repr__

        
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
