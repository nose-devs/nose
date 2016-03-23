"""
This plugin captures stdout during test execution. If the test fails
or raises an error, the captured output will be appended to the error
or failure output. It is enabled by default but can be disabled with
the options ``-s`` or ``--nocapture``.

:Options:
  ``--nocapture``
    Don't capture stdout (any stdout output will be printed immediately)

"""
import logging
import os
import sys
import traceback
from nose.plugins.base import Plugin
from nose.pyversion import exc_to_unicode, force_unicode
from nose.util import ln
from StringIO import StringIO


log = logging.getLogger(__name__)

class Capture(Plugin):
    """
    Output capture plugin. Enabled by default. Disable with ``-s`` or
    ``--nocapture``. This plugin captures stdout during test execution,
    appending any output captured to the error or failure output,
    should the test fail or raise an error.
    """
    enabled = True
    env_opt = 'NOSE_NOCAPTURE'
    name = 'capture'
    score = 1600

    def __init__(self):
        self.stdout = []
        self._buf = None

    def options(self, parser, env):
        """Register commandline options
        """
        parser.add_option(
            "-s", "--nocapture", action="store_false",
            default=not env.get(self.env_opt), dest="capture",
            help="Don't capture stdout (any stdout output "
            "will be printed immediately) [NOSE_NOCAPTURE]")

    def configure(self, options, conf):
        """Configure plugin. Plugin is enabled by default.
        """
        self.conf = conf
        if not options.capture:
            self.enabled = False

    def afterTest(self, test):
        """Clear capture buffer.
        """
        self.end()
        self._buf = None

    def begin(self):
        """Replace sys.stdout with capture buffer.
        """
        self.start() # get an early handle on sys.stdout

    def beforeTest(self, test):
        """Flush capture buffer.
        """
        self.start()

    def formatError(self, test, err):
        """Add captured output to error report.
        """
        test.capturedOutput = output = ''
        output_exc_info = None
        try:
            test.capturedOutput = output = self.buffer
        except UnicodeError:
            # python2's StringIO.StringIO [1] class has this warning:
            #
            #     The StringIO object can accept either Unicode or 8-bit strings,
            #     but mixing the two may take some care. If both are used, 8-bit
            #     strings that cannot be interpreted as 7-bit ASCII (that use the
            #     8th bit) will cause a UnicodeError to be raised when getvalue()
            #     is called.
            #
            # This exception handler is a protection against issue #816 [2].
            # Capturing the exception info allows us to display it back to the
            # user.
            #
            # [1] <https://github.com/python/cpython/blob/2.7/Lib/StringIO.py#L258>
            # [2] <https://github.com/nose-devs/nose/issues/816>
            output_exc_info = sys.exc_info()
        self._buf = None
        if (not output) and (not output_exc_info):
            # Don't return None as that will prevent other
            # formatters from formatting and remove earlier formatters
            # formats, instead return the err we got
            return err
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, output, output_exc_info=output_exc_info), tb)

    def formatFailure(self, test, err):
        """Add captured output to failure report.
        """
        return self.formatError(test, err)

    def addCaptureToErr(self, ev, output, output_exc_info=None):
        # If given, output_exc_info should be a 3-tuple from sys.exc_info(),
        # from an exception raised while trying to get the captured output.
        ev = exc_to_unicode(ev)
        output = force_unicode(output)
        error_text = [ev, ln(u'>> begin captured stdout <<'),
                      output, ln(u'>> end captured stdout <<')]
        if output_exc_info:
            error_text.extend([u'OUTPUT ERROR: Could not get captured output.',
                               # <https://github.com/python/cpython/blob/2.7/Lib/StringIO.py#L258>
                               # <https://github.com/nose-devs/nose/issues/816>
                               u"The test might've printed both 'unicode' strings and non-ASCII 8-bit 'str' strings.",
                               ln(u'>> begin captured stdout exception traceback <<'),
                               u''.join(traceback.format_exception(*output_exc_info)),
                               ln(u'>> end captured stdout exception traceback <<')])
        return u'\n'.join(error_text)

    def start(self):
        self.stdout.append(sys.stdout)
        self._buf = StringIO()
        # Python 3's StringIO objects don't support setting encoding or errors
        # directly and they're already set to None.  So if the attributes
        # already exist, skip adding them.
        if (not hasattr(self._buf, 'encoding') and
                hasattr(sys.stdout, 'encoding')):
            self._buf.encoding = sys.stdout.encoding
        if (not hasattr(self._buf, 'errors') and
                hasattr(sys.stdout, 'errors')):
            self._buf.errors = sys.stdout.errors
        sys.stdout = self._buf

    def end(self):
        if self.stdout:
            sys.stdout = self.stdout.pop()

    def finalize(self, result):
        """Restore stdout.
        """
        while self.stdout:
            self.end()

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    buffer = property(_get_buffer, None, None,
                      """Captured stdout output.""")
