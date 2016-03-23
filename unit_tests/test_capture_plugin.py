# -*- coding: utf-8 -*-
import sys
import unittest
from optparse import OptionParser
from nose.config import Config
from nose.plugins.capture import Capture
from nose.pyversion import force_unicode

if sys.version_info[0] == 2:
    py2 = True
else:
    py2 = False

class TestCapturePlugin(unittest.TestCase):

    def setUp(self):
        self._stdout = sys.stdout

    def tearDown(self):
        sys.stdout = self._stdout

    def test_enabled_by_default(self):
        c = Capture()
        assert c.enabled

    def test_can_be_disabled(self):
        c = Capture()
        parser = OptionParser()
        c.addOptions(parser)
        options, args = parser.parse_args(['test_can_be_disabled',
                                           '-s'])
        c.configure(options, Config())
        assert not c.enabled

        c = Capture()
        options, args = parser.parse_args(['test_can_be_disabled_long',
                                           '--nocapture'])
        c.configure(options, Config())
        assert not c.enabled

        env = {'NOSE_NOCAPTURE': 1}
        c = Capture()
        parser = OptionParser()
        c.addOptions(parser, env)
        options, args = parser.parse_args(['test_can_be_disabled'])
        c.configure(options, Config())
        assert not c.enabled

        c = Capture()
        parser = OptionParser()
        c.addOptions(parser)
        
        options, args = parser.parse_args(['test_can_be_disabled'])
        c.configure(options, Config())
        assert c.enabled
        
    def test_captures_stdout(self):
        c = Capture()
        c.start()
        print "Hello"
        c.end()
        self.assertEqual(c.buffer, "Hello\n")
        
    def test_captures_nonascii_stdout(self):
        c = Capture()
        c.start()
        print "test 日本"
        c.end()
        self.assertEqual(c.buffer, "test 日本\n")

    def test_does_not_crash_with_mixed_unicode_and_nonascii_str(self):
        class Dummy:
            pass
        d = Dummy()
        c = Capture()
        c.start()
        printed_nonascii_str = force_unicode("test 日本").encode('utf-8')
        printed_unicode = force_unicode("Hello")
        print printed_nonascii_str
        print printed_unicode
        try:
            raise Exception("boom")
        except:
            err = sys.exc_info()
        formatted = c.formatError(d, err)
        _, fev, _ = formatted

        if py2:
            for string in [force_unicode(printed_nonascii_str, encoding='utf-8'), printed_unicode]:
                assert string not in fev, "Output unexpectedly found in error message"
            assert d.capturedOutput == '', "capturedOutput unexpectedly non-empty"
            assert "OUTPUT ERROR" in fev
            assert "captured stdout exception traceback" in fev
            assert "UnicodeDecodeError" in fev
        else:
            for string in [repr(printed_nonascii_str), printed_unicode]:
                assert string in fev, "Output not found in error message"
                assert string in d.capturedOutput, "Output not attached to test"

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
        (fec, fev, ftb) = formatted
        # print fec, fev, ftb
        
        self.assertEqual(ec, fec)
        self.assertEqual(tb, ftb)
        assert 'Oh my!' in fev, "Output not found in error message"
        assert 'Oh my!' in d.capturedOutput, "Output not attached to test"

    def test_format_nonascii_error(self):
        class Dummy:
            pass
        d = Dummy()
        c = Capture()
        c.start()
        try:
            print "debug 日本"
            raise AssertionError(u'response does not contain 名')
        except:
            err = sys.exc_info()
        formatted = c.formatError(d, err)

    def test_captured_stdout_has_encoding_attribute(self):
        c = Capture()
        c.start()
        self.assertNotEqual(sys.stdout, sys.__stdout__)
        self.assertTrue(hasattr(sys.stdout, 'encoding'))
        c.end()

if __name__ == '__main__':
    unittest.main()
