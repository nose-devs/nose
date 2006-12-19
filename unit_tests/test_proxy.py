import sys
import unittest
from nose.config import Config
from nose.proxy import *
from nose.result import Result, start_capture, end_capture


class dummy:
    def __init__(self):
        self.buf = []
    def write(self, val):
        if val is None:
            return
        if not self.buf:
            self.buf.append('')
        self.buf[-1] += val
    def writeln(self, val=None):
        self.write(val)
        self.buf.append('')
        

class TestNoseProxy(unittest.TestCase):

    class TC(unittest.TestCase):
        def runTest(self):
            print "RUNTEST %s" % self
            pass

    class ErrTC(unittest.TestCase):
        def test_err(self):
            print "Ahoy there!"
            raise Exception("oh well")

        def test_fail(self):
            a = 1
            print "a:", a
            assert a == 2
        
    def setUp(self):
        self.real_conf = Result.conf
        start_capture()
        
    def tearDown(self):
        Result.conf = self.real_conf
        end_capture()

    def test_proxy_result(self):
        # set up configuration at class level
        Result.conf = Config()
        
        res = unittest.TestResult()
        pr = ResultProxy(res)

        # start is proxied
        test = self.TC()
        pr.startTest(test)
        self.assertEqual(res.testsRun, 1)
        
        # success is proxied        
        pr.addSuccess(test)
        self.assertEqual(res.errors, [])
        self.assertEqual(res.failures, [])
        
        # stop is proxied
        pr.stopTest(test)

        # error is proxied
        try:
            raise Exception("oh no!")
        except:
            e = sys.exc_info()
        pr.addError(test, e)
        
        # failure is proxied
        try:
            raise AssertionError("not that!")
        except:
            e = sys.exc_info()
        pr.addFailure(test, e)

        self.assertEqual(len(res.errors), 1)
        self.assertEqual(len(res.failures), 1)        

        # shouldStop is proxied
        self.assertEqual(pr.shouldStop, res.shouldStop)
        pr.shouldStop = True
        assert res.shouldStop
            
    def test_output_capture(self):

        c = Config()
        c.capture = True
        c.detailedErrors = True
        Result.conf = c
        
        res = unittest.TestResult()
        pr = ResultProxy(res)
                        
        errcase = self.ErrTC('test_err')
        failcase = self.ErrTC('test_fail')
        errcase.run(pr)
        failcase.run(pr)

        assert len(res.errors) == 1
        assert len(res.failures) == 1

        err = res.errors[0][1]

        assert 'Ahoy there!' in err

        fail = res.failures[0][1]
        assert 'a: 1' in fail
        assert '>>  assert 1 == 2' in fail
        
    def test_proxy_suite(self):
        c = Config()
        c.capture = True
        c.detailedErrors = True
        Result.conf = c
        
        errcase = self.ErrTC('test_err')
        failcase = self.ErrTC('test_fail')
        passcase = self.TC()

        suite = ResultProxySuite([errcase, failcase, passcase])
        print list(suite)
        
        for test in suite:
            print test
            assert isinstance(test, TestProxy)
        
        d = dummy()    
        res = unittest._TextTestResult(d, 1, 1)
        suite.run(res)
        res.printErrors()
        print d.buf

        # split internal \n in strings into own lines
        buf = '\n'.join(d.buf).split('\n')
                
        assert 'Ahoy there!' in buf
        assert 'a: 1' in buf
        assert '>>  assert 1 == 2' in buf
        assert buf.index('>>  assert 1 == 2') < buf.index('a: 1')
        
    def test_proxy_test(self):
        c = Config()
        c.capture = True
        c.detailedErrors = True
        Result.conf = c

        base_errcase = self.ErrTC('test_err')
        base_failcase = self.ErrTC('test_fail')
        base_passcase = self.TC()
        errcase = TestProxy(base_errcase)
        failcase = TestProxy(base_failcase)
        passcase = TestProxy(base_passcase)

        self.assertEqual(errcase.id(), base_errcase.id())
        self.assertEqual(failcase.id(), base_failcase.id())
        self.assertEqual(passcase.id(), base_passcase.id())

        self.assertEqual(errcase.shortDescription(),
                         base_errcase.shortDescription())
        self.assertEqual(failcase.shortDescription(),
                         base_failcase.shortDescription())
        self.assertEqual(passcase.shortDescription(),
                         base_passcase.shortDescription())
        
        d = dummy()
        
        res = unittest._TextTestResult(d, 1, 1)

        errcase.run(res)
        failcase.run(res)
        passcase.run(res)
        
        #print >>sys.stderr, res.errors
        #print >>sys.stderr, res.failures

        res.printErrors()

        # split internal \n in strings into own lines
        buf = '\n'.join(d.buf).split('\n')
                
        assert 'Ahoy there!' in buf
        assert 'a: 1' in buf
        assert '>>  assert 1 == 2' in buf
        assert buf.index('>>  assert 1 == 2') < buf.index('a: 1')
        
        
if __name__ == '__main__':
    unittest.main()
