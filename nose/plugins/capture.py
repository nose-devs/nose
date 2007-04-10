import os
import sys
from nose.plugins.base import Plugin
from nose.util import ln
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Capture(Plugin):
    """Output capture plugin. Enabled by default. Disable with -s or
    --nocapture. This plugin captures stdout during test execution,
    appending any output capture to the error or failure output,
    should the test fail or raise an error.
    """
    enabled = True
    env_opt = 'NOSE_NOCAPTURE'
    name = 'capture'
    score = 50
    
    def __init__(self):
        self.stdout = None
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

    def begin(self):
        self.start() # get an early handle on sys.stdout

    def beforeTest(self, test):
        self.start()
        
    def formatError(self, test, err):
        self.end()
        test.captured_output = output = self.buffer
        if not output:
            return
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, output), tb)        

    def formatFailure(self, test, err):
        return self.formatError(test, err)

    def addCaptureToErr(self, ev, output):
        return '\n'.join([str(ev) , ln('>> begin captured stdout <<'),
                          output, ln('>> end captured stdout <<')])

    def start(self):
        self._buf = StringIO()
        if self.stdout is None:
            self.stdout = sys.stdout
        sys.stdout = self._buf

    def end(self):
        if self.stdout:
            sys.stdout = self.stdout
            self.stdout = None

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    buffer = property(_get_buffer, None, None,
                      """Captured stdout output.""")

    def __del__(self):
        self.end()
