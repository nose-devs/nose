"""
This plugin captures stdout during test execution, appending any
output captured to the error or failure output, should the test fail
or raise an error. It is enabled by default but may be disable with
the options -s or --nocapture.
"""
import logging
import os
import sys
from nose.plugins.base import Plugin
from nose.util import ln
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


log = logging.getLogger(__name__)

class Capture(Plugin):
    """
    Output capture plugin. Enabled by default. Disable with -s or
    --nocapture. This plugin captures stdout during test execution,
    appending any output captured to the error or failure output,
    should the test fail or raise an error.
    """
    enabled = True
    env_opt = 'NOSE_NOCAPTURE'
    name = 'capture'
    score = 500
    
    def __init__(self):
        self.stdout = []
        self._buf = None

    def options(self, parser, env=os.environ):
        parser.add_option(
            "-s", "--nocapture", action="store_false",
            default=not env.get(self.env_opt), dest="capture",
            help="Don't capture stdout (any stdout output "
            "will be printed immediately) [NOSE_NOCAPTURE]")

    def configure(self, options, conf):
        self.conf = conf
        if not options.capture:
            self.enabled = False

    def afterTest(self, test):
        self.end()
        self._buf = None
        
    def begin(self):
        self.start() # get an early handle on sys.stdout

    def beforeTest(self, test):
        self.start()
        
    def formatError(self, test, err):
        test.capturedOutput = output = self.buffer
        self._buf = None
        if not output:
            # Don't return None as that will prevent other
            # formatters from formatting and remove earlier formatters
            # formats, instead return the err we got
            return err 
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, output), tb)

    def formatFailure(self, test, err):
        return self.formatError(test, err)

    def addCaptureToErr(self, ev, output):
        return '\n'.join([str(ev) , ln('>> begin captured stdout <<'),
                          output, ln('>> end captured stdout <<')])

    def start(self):
        self.stdout.append(sys.stdout)
        self._buf = StringIO()
        sys.stdout = self._buf

    def end(self):
        if self.stdout:
            sys.stdout = self.stdout.pop()

    def finalize(self, result):
        while self.stdout:
            self.end()

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    buffer = property(_get_buffer, None, None,
                      """Captured stdout output.""")
