import unittest
from nose.plugins.skip import Skip, SkipTest
from StringIO import StringIO


class TestSkipPlugin(unittest.TestCase):

    def test_api_present(self):
        sk = Skip()
        sk.addOptions
        sk.configure
        sk.prepareTestResult

    def test_prepare_patches_result(self):
        stream = unittest._WritelnDecorator(StringIO())
        res = unittest._TextTestResult(stream, 0, 1)
        sk = Skip()
        sk.prepareTestResult(res)
        res._orig_addError
        res._orig_printErrors
        res.skipped
        self.assertEqual(res.errorClasses,
                         {SkipTest: ('skipped', 'SKIP')})

        # result w/out print works too
        res = unittest.TestResult()
        sk = Skip()
        sk.prepareTestResult(res)
        res._orig_addError
        res.skipped
        self.assertEqual(res.errorClasses,
                         {SkipTest: ('skipped', 'SKIP')})

    def test_patched_result_handles_skip(self):
        res = unittest.TestResult()
        sk = Skip()
        sk.prepareTestResult(res)

        class TC(unittest.TestCase):
            def test(self):
                raise SkipTest('skip me')

        test = TC('test')
        test(res)
        assert not res.errors, "Skip was not caught: %s" % res.errors
        assert res.skipped
        assert res.skipped[0][0] is test

    def test_skip_output(self):
        class TC(unittest.TestCase):
            def test(self):
                raise SkipTest('skip me')

        stream = unittest._WritelnDecorator(StringIO())
        res = unittest._TextTestResult(stream, 0, 1)
        sk = Skip()
        sk.prepareTestResult(res)

        test = TC('test')
        test(res)
        assert not res.errors, "Skip was not caught: %s" % res.errors
        assert res.skipped            

        res.printErrors()
        out = stream.getvalue()
        assert out
        assert out.startswith('S')
        assert 'SKIP: ' in out
        assert 'skip me' in out
        assert res.wasSuccessful

    def test_skip_output_verbose(self):

        class TC(unittest.TestCase):
            def test(self):
                raise SkipTest('skip me too')
        
        stream = unittest._WritelnDecorator(StringIO())
        res = unittest._TextTestResult(stream, 0, verbosity=2)
        sk = Skip()
        sk.prepareTestResult(res)
        test = TC('test')
        test(res)
        assert not res.errors, "Skip was not caught: %s" % res.errors
        assert res.skipped            

        res.printErrors()
        out = stream.getvalue()
        print out
        assert out

        assert ' ... SKIP' in out
        assert 'skip me too' in out
        

if __name__ == '__main__':
    unittest.main()
