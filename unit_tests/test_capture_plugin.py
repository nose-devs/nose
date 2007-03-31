import sys
import unittest
from nose.plugins.capture import Capture

class TestCapturePlugin(unittest.TestCase):

    def test_captures_stdout(self):
        c = Capture()
        c.start()
        print "Hello"
        c.end()
        self.assertEqual(c.buffer, "Hello\n")

    def test_format_error(self):
        class Dummy:
            pass
        d = Dummy()
        c = Capture()
        c.start()
        try:
            print "Oh my!"
            raise Exception("boom")
        except:
            err = sys.exc_info()
        formatted = c.formatError(d, err)
        ec, ev, tb = err
        fec, fev, ftb = formatted
        self.assertEqual(ec, fec)
        self.assertEqual(tb, ftb)

        assert 'Oh my!' in fev
        assert 'Oh my!' in d.captured_output

if __name__ == '__main__':
    unittest.main()
