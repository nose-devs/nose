import imp
import sys
import unittest
from nose.context import FixtureContext

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
        cx = FixtureContext()
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
        cx = FixtureContext()
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
        cx = FixtureContext()
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
        cx = FixtureContext()
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
        cx = FixtureContext()
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
        cx = FixtureContext()
        in_context = cx.add(mod, case)
        result = unittest.TestResult()
        in_context(result)
        assert not result.errors, result.errors        
        assert case.state == ['setUp', 'runTest', 'tearDown']
        assert mod.state == ['setUp', 'tearDown']

        # multiple test cases from the module
        result = unittest.TestResult()
        mod.state = []
        cx = FixtureContext()
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
        cx = FixtureContext()
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

        class TestClass:
            class_setup = None
            class_teardown = None
            inst_setup = []
            inst_teardown = []

            def setup(self):
                print "TestClass.setup"
                self.inst_setup.append(self)

            def teardown(self):
                print "TestClass.teardown"
                self.inst_teardown.append(self)

            def setup_class(cls):
                cls.class_setup = 1
                cls.class_teardown = 0
            setup_class = classmethod(setup_class)

            def teardown_class(cls):
                cls.class_teardown = 1
            teardown_class = classmethod(teardown_class)

            def test_method(self):
                pass

        # Inner classes aren't supported, so make it look like
        # a module-level class
        mod = imp.new_module('mod')
        mod.TestClass = TestClass
        TestClass.__module__ = 'mod'
        sys.modules['mod'] = mod
        
        context = FixtureContext()
        case = MethodTestCase(TestClass.test_method)
        in_context = context(case)
        result = unittest.TestResult()
        in_context(result)

        assert not result.errors, result.errors
        
        assert TestClass.class_setup == 1, "Class setup_class was not called"
        assert TestClass.class_teardown == 1, \
            "Class teardown_class was not called"
        assert TestClass.inst_setup, "Instance setup was not called"
        assert TestClass.inst_teardown, "Instance teardown was not called"

    def test_context_setup_err(self):

        def setup():
            raise Exception("Oh no! setup failed.")
        
        def test_a():
            pass

        def test_b():
            raise Exception("Should not be run")

        mod = imp.new_module('mod_setup_err')
        mod.setup = setup
        setup.__module__ = 'mod_setup_err'
        mod.test_a = test_a
        test_a.__module__ = 'mod_setup_err'
        mod.test_b = test_b
        test_b.__module = 'mod_setup_err'
        sys.modules['mod_setup_err'] = mod

        context = FixtureContext()
        a = FunctionTestCase(mod.test_a)
        b = FunctionTestCase(mod.test_b)

        case_a = context(a)
        case_b = context(b)

        res = unittest.TestResult()
        case_a(res)
        assert res.errors
        assert len(res.errors) == 1
        

if __name__ == '__main__':
    unittest.main()
