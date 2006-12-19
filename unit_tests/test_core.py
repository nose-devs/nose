import unittest
import nose.core

from cStringIO import StringIO

def nullcollector(conf, loader):
    def nulltest(result):
        pass
    return nulltest

class TestTestProgram(unittest.TestCase):

    def test_init_arg_defaultTest(self):
        try:
            t = nose.core.TestProgram(defaultTest='something', argv=[], env={})
        except ValueError:
            pass
        else:
            self.fail("TestProgram with non-callable defaultTest should "
                      "have thrown ValueError")

    def test_init_arg_module(self):
        s = StringIO()
        t = nose.core.TestProgram('__main__', defaultTest=nullcollector,
                                  argv=[], env={}, stream=s)
        assert '__main__' in t.conf.tests


class TestAPI_run(unittest.TestCase):

    def test_restore_stdout(self):
        import sys
        s = StringIO()
        stdout = sys.stdout
        res = nose.core.run(defaultTest=nullcollector, argv=[], env={},
                            stream=s)
        stdout_after = sys.stdout
        self.assertEqual(stdout, stdout_after)
        
if __name__ == '__main__':
    unittest.main()
