import sys
import unittest
import nose.result
from nose.config import Config
from nose.fixture import Context
from nose.exc import DeprecatedTest, SkipTest
from nose.result import start_capture, end_capture

class TestResult(unittest.TestCase):

    class _T(unittest.TestCase):
        def runTest(self):
            pass

    def T(self):
        ctx = Context()
        case = self._T()
        return ctx(case)
        
    def setUp(self):
        self.buf = []
        class dummy:
            pass
        stream = dummy()
        stream.write = self.buf.append
        stream.writeln = self.buf.append
        self.tr = nose.result.TextTestResult(stream, None, 2, Config())

#    def tearDown(self):
#        nose.result.end_capture()
        
    def test_capture(self):
        start_capture()
        try:
            print "Hello"
            self.assertEqual(sys.stdout.getvalue(), "Hello\n")
        finally:
            end_capture()
        
    def test_init(self):
        tr = self.tr
        self.assertEqual(tr.errors, [])
        self.assertEqual(tr.failures, [])
        self.assertEqual(tr.deprecated, [])
        self.assertEqual(tr.skip, [])
        self.assertEqual(tr.testsRun, 0)
        self.assertEqual(tr.shouldStop, 0)
        
    def test_add_error(self):
        buf, tr = self.buf, self.tr
        try:
            raise Exception("oh no!")
        except:
            err = sys.exc_info()            
        test = self.T()
        tr.addError(test, err)
        self.assertEqual(tr.errors[0],
                         (test, tr._exc_info_to_string(err, test), ''))
        self.assertEqual(buf, [ 'ERROR' ])

        # test with capture
        start_capture()
        try:
            tr.capture = True
            print "some output"
            tr.addError(test, err)
            self.assertEqual(tr.errors[1],
                             (test, tr._exc_info_to_string(err, test),
                              'some output\n'))
            self.assertEqual(buf, [ 'ERROR', 'ERROR' ])
        finally:
            end_capture()

        # test deprecated
        try:
            raise DeprecatedTest("deprecated")
        except:
            err = sys.exc_info()
        tr.addError(test, err)
        self.assertEqual(len(tr.errors), 2)
        self.assertEqual(tr.deprecated, [ (test, '', '') ])

        # test skip
        try:
            raise SkipTest("skip")
        except:
            err = sys.exc_info()
        tr.addError(test, err)
        self.assertEqual(len(tr.errors), 2)
        self.assertEqual(tr.skip, [ (test, '', '') ])
        self.assertEqual(buf, ['ERROR', 'ERROR', 'DEPRECATED', 'SKIP'])
        
    def test_add_failure(self):
        buf, tr = self.buf, self.tr
        try:
            assert False, "test add fail"
        except:
            err = sys.exc_info()            
        test = self.T()
        tr.addFailure(test, err)
        self.assertEqual(tr.failures[0],
                         (test, tr._exc_info_to_string(err, test), ''))
        self.assertEqual(buf, [ 'FAIL' ])

        # test with capture
        start_capture()
        try:
            tr.capture = True
            print "some output"
            tr.addFailure(test, err)
            self.assertEqual(tr.failures[1],
                             (test, tr._exc_info_to_string(err, test),
                              'some output\n'))
            self.assertEqual(buf, [ 'FAIL', 'FAIL' ])
        finally:
            end_capture()

    def test_start_stop(self):
        tr = self.tr
        test = self.T()
        tr.startTest(test)
        tr.stopTest(test)

    def test_stop_on_error(self):
        buf, tr = self.buf, self.tr
        tr.conf.stopOnError = True
        try:
            raise Exception("oh no!")
        except:
            err = sys.exc_info()
        test = self.T()
        tr.addError(test, err)        
        assert tr.shouldStop

    def test_stop_on_error_skip(self):
        buf, tr = self.buf, self.tr
        tr.conf.stopOnError = True
        try:
            raise SkipTest("oh no!")
        except:
            err = sys.exc_info()
        test = self.T()
        tr.addError(test, err)        
        assert not tr.shouldStop

    def test_stop_on_error_deprecated(self):
        buf, tr = self.buf, self.tr
        tr.conf.stopOnError = True
        try:
            raise DeprecatedTest("oh no!")
        except:
            err = sys.exc_info()
        test = self.T()
        tr.addError(test, err)        
        assert not tr.shouldStop
        
    def test_stop_on_error_fail(self):
        buf, tr = self.buf, self.tr
        tr.conf.stopOnError = True
        try:
            assert False, "test add fail"
        except:
            err = sys.exc_info()            
        test = self.T()
        tr.addFailure(test, err)        
        assert tr.shouldStop
        
if __name__ == '__main__':
    unittest.main()
