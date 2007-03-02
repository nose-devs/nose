import imp
import sys
import unittest
from nose.fixture import Context

class TestFixtureContext(unittest.TestCase):

    def test_case_proxy(self):
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
            def runTest(self):
                self.state += ['runTest']
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']
        
        case = TC()
        cx = Context()
        in_context = cx.add(__name__, case)
        
        result = unittest.TestResult()
        in_context(result)
        print result.errors
        self.assertEqual(case.state, ['setUp', 'runTest', 'tearDown'])

    def test_call(self):
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']
        case = TC('testSomething')
        cx = Context()
        in_context = cx(case)
        result = unittest.TestResult()
        in_context(result)
        print result.errors
        self.assertEqual(case.state, ['setUp', 'testSomething', 'tearDown'])

    def test_case_proxy_test_method(self):
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']
                
        case = TC('testSomething')
        cx = Context()
        in_context = cx.add(__name__, case)
        result = unittest.TestResult()
        in_context(result)
        print result.errors
        self.assertEqual(case.state, ['setUp', 'testSomething', 'tearDown'])

    def test_case_error(self):
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
            def runTest(self):
                self.state += ['runTest']
                raise TypeError("Some error")
            
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']
        
        case = TC()
        cx = Context()
        in_context = cx.add(__name__, case)
        
        result = unittest.TestResult()
        in_context(result)        
        assert result.errors
        self.assertEqual(case.state, ['setUp', 'runTest', 'tearDown'])

    def test_case_setup_error(self):
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
                raise TypeError("Some error")
            def runTest(self):
                self.state += ['runTest']            
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']
        
        case = TC()
        cx = Context()
        in_context = cx.add(__name__, case)
        
        result = unittest.TestResult()
        in_context(result)        
        assert result.errors
        self.assertEqual(case.state, ['setUp'])
        
    def test_module_setup(self):
        """Test that module fixtures execute at proper times.

        This includes packages and subpackages; the fixtures for pack.sub
        should execute according to the package hierarchy::

          pack.setup()
            pack.sub.setup()
              pack.sub tests
            pack.sub.teardown()
          pack.teardown()        
        """
        def setup(m):
            m.state += ['setUp']
        def teardown(m):
            m.state += ['tearDown']
            
        class TC(unittest.TestCase):
            state = None
            def setUp(self):
                self.state = ['setUp']
            def errTest(self):
                self.state += ['errTest']
                raise TypeError("an error")
            def failTest(self):
                self.state += ['failTest']
                assert False, "Fail the test"
            def runTest(self):
                self.state += ['runTest']
            def tearDown(self):
                self.state += ['tearDown']
            def testSomething(self):
                self.state += ['testSomething']        
                
        mod = imp.new_module('test_module')
        sys.modules['test_module'] = mod
        mod.state = []
        mod.setup = setup
        mod.teardown = teardown
        mod.TC = TC
        case = mod.TC()
        err = mod.TC('errTest')
        fail = mod.TC('failTest')

        # module with only one test collected
        cx = Context()
        in_context = cx.add(mod, case)
        result = unittest.TestResult()
        in_context(result)
        assert not result.errors, result.errors        
        assert case.state == ['setUp', 'runTest', 'tearDown']
        assert mod.state == ['setUp', 'tearDown']

        # multiple test cases from the module
        result = unittest.TestResult()
        mod.state = []
        cx = Context()
        in_context = cx.add(mod, case)
        err_context = cx.add(mod, err)
        fail_context = cx.add(mod, fail)

        in_context(result)
        assert not result.errors, result.errors        
        self.assertEqual(case.state, ['setUp', 'runTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp'])

        err_context(result)
        assert result.errors
        self.assertEqual(err.state, ['setUp', 'errTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp'])

        fail_context(result)
        assert result.failures
        self.assertEqual(fail.state, ['setUp', 'failTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp', 'tearDown'])

        # submodule
        submod = imp.new_module('test_module.more_tests')
        sys.modules['test_module.more_tests'] = submod
        submod.state = []
        submod.setup = setup
        submod.teardown = teardown
        submod.TC = TC
        mod.more_tests = submod

        mod.state = []
        result = unittest.TestResult()
        cx = Context()
        mod_case = mod.TC()
        mod_err = mod.TC('errTest')
        mod_fail = mod.TC('failTest')
        mod_in_context = cx.add(mod, mod_case)
        mod_err_context = cx.add(mod, mod_err)
        mod_fail_context = cx.add(mod, mod_fail)

        submod_case = submod.TC()
        submod_err = submod.TC('errTest')
        submod_fail = submod.TC('failTest')
        submod_in_context = cx.add(submod, submod_case)
        submod_err_context = cx.add(submod, submod_err)
        submod_fail_context = cx.add(submod, submod_fail)        

        # run the submodule tests first
        submod_in_context(result)
        assert not result.errors, result.errors        
        self.assertEqual(submod_case.state, ['setUp', 'runTest', 'tearDown'])
        self.assertEqual(submod.state, ['setUp'])
        self.assertEqual(mod.state, ['setUp'])

        submod_err_context(result)
        assert result.errors
        self.assertEqual(submod_err.state, ['setUp', 'errTest', 'tearDown'])
        self.assertEqual(submod.state, ['setUp'])
        self.assertEqual(mod.state, ['setUp'])
        
        submod_fail_context(result)
        assert result.failures
        self.assertEqual(submod_fail.state, ['setUp', 'failTest', 'tearDown'])
        self.assertEqual(submod.state, ['setUp', 'tearDown'])        
        self.assertEqual(mod.state, ['setUp'])

        # then the module tests
        mod_in_context(result)
        assert result.errors
        self.assertEqual(mod_case.state, ['setUp', 'runTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp'])
        self.assertEqual(submod.state, ['setUp', 'tearDown'])        

        mod_err_context(result)
        assert result.errors
        self.assertEqual(mod_err.state, ['setUp', 'errTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp'])
        self.assertEqual(submod.state, ['setUp', 'tearDown'])
        
        mod_fail_context(result)
        assert result.failures
        self.assertEqual(mod_fail.state, ['setUp', 'failTest', 'tearDown'])
        self.assertEqual(mod.state, ['setUp', 'tearDown'])        
        self.assertEqual(submod.state, ['setUp', 'tearDown'])


    def test_class_setup(self):
        """Test that per-class and per-instance fixtures execute correctly.

        Fixtures are supported at the class and instance level for test
        classes. They should execute in the following order::

          Class.setup_class()
            instance.setup()
              instance test
            instance.teardown()
            ...
          Class.teardown_class()
        """
        from nose.case import MethodTestCase
        
        inst_setup = []
        inst_teardown = []
        class TestClass:
            setup = None
            teardown = None

            def setup(self):
                inst_setup.append(self)

            def teardown(self):
                inst_teardown.append(self)

            def setup_class(cls):
                cls.setup = 1
                cls.teardown = 0
            setup_class = classmethod(setup_class)

            def teardown_class(cls):
                cls.teardown = 1
            teardown_class = classmethod(teardown_class)

            def test_method(self):
                pass

        context = Context()
        case = MethodTestCase(TestClass.test_method)
        in_context = context(case)
        result = unittest.TestResult()
        in_context(result)

        assert TestClass.setup == 1, "Class setup_class was not called"
        assert TestClass.teardown == 1, "Class teardown_class was not called"
        assert inst_setup, "Instance setup was not called"
        assert inst_teardown, "Instance teardown was not called"

if __name__ == '__main__':
    unittest.main()
