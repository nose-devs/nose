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
from nose.plugins.base import Plugin
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
    capture_stderr = False
    env_opt = 'NOSE_NOCAPTURE'
    name = 'capture'
    score = 1600

    def __init__(self):
        self.stdout = []
        self.stderr = []
        self._stdout_buf = None
        self._stderr_buf = None

    def options(self, parser, env):
        """Register commandline options
        """
        parser.add_option(
            "-s", "--nocapture", action="store_false",
            default=not env.get(self.env_opt), dest="capture",
            help="Don't capture stdout (any stdout output "
            "will be printed immediately) [NOSE_NOCAPTURE]")
        parser.add_option(
            "--capture-stderr", action="store_true",
            default=False, dest="capture_stderr",
            help="Also capture stderr")

    def configure(self, options, conf):
        """Configure plugin. Plugin is enabled by default.
        """
        self.conf = conf
        if not options.capture:
            self.enabled = False
        self.capture_stderr = options.capture_stderr

    def afterTest(self, test):
        """Clear capture buffer.
        """
        self.end()
        self._stdout_buf = None
        self._stderr_buf = None

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
        test.capturedOutput = stdout = self.stdout_buffer
        stderr = self.stderr_buffer
        self._stdout_buf = None
        self._stderr_buf = None

        if not stdout and not stderr:
            # Don't return None as that will prevent other
            # formatters from formatting and remove earlier formatters
            # formats, instead return the err we got
            return err
        ec, ev, tb = err
        ev_plus_captured = [self.evToUnicode(ev),
                            self.formatCapturedOutput(stdout)]
        if self.capture_stderr:
            ev_plus_captured.append(self.formatCapturedOutput(stderr, u'stderr'))

        return (ec,  u'\n'.join(ev_plus_captured), tb)

    def formatFailure(self, test, err):
        """Add captured output to failure report.
        """
        return self.formatError(test, err)

    def evToUnicode(self, ev):
        if isinstance(ev, Exception):
            if hasattr(ev, '__unicode__'):
                # 2.6+
                ev = unicode(ev)
            else:
                # 2.5-
                if not hasattr(ev, 'message'):
                    # 2.4
                    msg = len(ev.args) and ev.args[0] or ''
                else:
                    msg = ev.message
                if (isinstance(msg, basestring) and
                    not isinstance(msg, unicode)):
                    msg = msg.decode('utf8', 'replace')
                ev = u'%s: %s' % (ev.__class__.__name__, msg)
        return u'\n'.join([ev])

    def formatCapturedOutput(self, output, which_pipe=u'stdout'):
        if not isinstance(output, unicode):
            output = output.decode('utf8', 'replace')
        return u'\n'.join([ln(u'>> begin captured %s <<' % which_pipe),
                           output,
                           ln(u'>> end captured %s <<' % which_pipe)])

    def start(self):
        self.stdout.append(sys.stdout)
        self._stdout_buf = StringIO()
        sys.stdout = self._stdout_buf
        if self.capture_stderr:
            self.stderr.append(sys.stderr)
            self._stderr_buf = StringIO()
            sys.stderr = self._stderr_buf

    def end(self):
        if self.stdout:
            sys.stdout = self.stdout.pop()
        if self.stderr:
            sys.stderr = self.stderr.pop()

    def finalize(self, result):
        """Restore stdout.
        """
        while self.stdout or self.stderr:
            self.end()

    def _get_stdout_buffer(self):
        if self._stdout_buf is not None:
            return self._stdout_buf.getvalue()

    stdout_buffer = property(_get_stdout_buffer, None, None,
                      """Captured stdout output.""")

    def _get_stderr_buffer(self):
        if self._stderr_buf is not None:
            return self._stderr_buf.getvalue()

    stderr_buffer = property(_get_stderr_buffer, None, None,
                      """Captured stderr output.""")
