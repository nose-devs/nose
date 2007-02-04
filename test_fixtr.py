import imp
import unittest
from fixtr import Context

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
        assert case.state == ['setUp', 'runTest', 'tearDown']

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
        assert case.state == ['setUp']
        
    def test_module_setup(self):
        
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

        
        
if __name__ == '__main__':
    unittest.main()
