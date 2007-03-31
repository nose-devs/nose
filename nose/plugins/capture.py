import sys
from nose.plugins.base import Plugin
from nose.util import ln
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Capture(Plugin):

    def __init__(self):
        self.stdout = None
        self._buf = None

    def begin(self):
        self.start() # get an early handle on sys.stdout

    def formatError(self, test, err):
        self.end()
        test.captured_output = output = self.buffer
        if not output:
            return
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, output), tb)        

    def formatFailure(self, test, err):
        return self.formatError(self, test, err)

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
