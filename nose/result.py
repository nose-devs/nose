"""Test result handlers. Base class (Result) implements plugin handling,
output capture, and assert introspection, and handles deprecated and skipped
tests. TextTestResult is a drop-in replacement for unittest._TextTestResult
that uses the capabilities in Result.
"""
import inspect
import logging
import pdb
import sys
import tokenize
from unittest import _TextTestResult, TestSuite
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from nose.inspector import inspect_traceback
from nose.exc import DeprecatedTest, SkipTest
from nose.plugins import call_plugins

# buffer = StringIO()
stdout = []

log = logging.getLogger('nose.result')

class Result(object):
    """Base class for results handlers.
    """
    capt = None
    conf = None
    tbinfo = None
    shouldStop = False
    
    def addDeprecated(self, test):
        self.resetBuffer()
        call_plugins(self.conf.plugins, 'addDeprecated', test)
        
    def addError(self, test, err):
        if self.isDeprecated(err):
            self.addDeprecated(test)
        elif self.isSkip(err):
            self.addSkip(test)
        else:
            self.capt = self.getBuffer()
            if self.conf.debugErrors:
                if self.conf.capture:
                    end_capture()
                pdb.post_mortem(err[2])
                if self.conf.capture:
                    start_capture()
            self.resetBuffer()
            call_plugins(self.conf.plugins, 'addError',
                         test, err, self.capt)
            if self.conf.stopOnError:
                self.shouldStop = True
            
    def addFailure(self, test, err):
        self.capt = self.getBuffer()
        if self.conf.debugFailures:
            if self.conf.capture:
                end_capture()
            pdb.post_mortem(err[2])
            if self.conf.capture:
                start_capture()
        if self.conf.detailedErrors:
            try:
                self.tbinfo = inspect_traceback(err[2])
            except tokenize.TokenError:
                self.tbinfo = "ERR: unable to inspect traceback"
        else:
            self.tbinfo = ''
        self.resetBuffer()
        call_plugins(self.conf.plugins, 'addFailure',
                     test, err, self.capt, self.tbinfo)
        if self.conf.stopOnError:
            self.shouldStop = True
        
    def addSkip(self, test):
        self.resetBuffer()
        call_plugins(self.conf.plugins, 'addSkip', test)

    def addSuccess(self, test):
        self.capt = self.getBuffer()
        self.resetBuffer()
        call_plugins(self.conf.plugins, 'addSuccess', test, self.capt)

    def getBuffer(self):
        if stdout:
            try:
                return sys.stdout.getvalue()
            except AttributeError:
                pass
        # capture is probably off
        return ''
        
    def isDeprecated(self, err):
        if err[0] is DeprecatedTest or isinstance(err[0], DeprecatedTest):
            return True
        return False
    
    def isSkip(self, err):
        if err[0] is SkipTest or isinstance(err[0], SkipTest):
            return True
        return False
        
    def resetBuffer(self):
        if stdout:
            sys.stdout.truncate(0)
            sys.stdout.seek(0)

    def startTest(self, test):
        if self.conf.capture:
            self.resetBuffer()
            self.capt = None
        self.tbinfo = None
        call_plugins(self.conf.plugins, 'startTest', test)
        
    def stopTest(self, test):
        if self.conf.capture:
            self.resetBuffer()
            self.capt = None
        self.tbinfo = None            
        call_plugins(self.conf.plugins, 'stopTest', test)


class TextTestResult(Result, _TextTestResult):
    """Text test result that extends unittest's default test result with
    several optional features:

      - output capture

        Capture stdout while tests are running, and print captured output with
        errors and failures.
      
      - debug on error/fail

        Drop into pdb on error or failure, in the frame where the exception
        was raised.
        
      - deprecated or skipped tests

        raise DeprecatedTest or SkipTest to indicated that a test is
        deprecated or has been skipped. Deprecated or skipped tests will be
        printed with errors and failures, but don't cause the test run as a
        whole to be considered non-successful.
    """    
    def __init__(self, stream, descriptions, verbosity, conf):        
        self.deprecated = []
        self.skip = []
        self.conf = conf
        self.capture = conf.capture
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
                
    def addDeprecated(self, test):
        Result.addDeprecated(self, test)
        self.deprecated.append((test, '', ''))
        self.writeRes('DEPRECATED','D')
        
    def addError(self, test, err):
        Result.addError(self, test, err)
        if not self.isDeprecated(err) and not self.isSkip(err):
            self.errors.append((test,
                                self._exc_info_to_string(err, test),
                                self.capt))
            self.writeRes('ERROR','E')
            
    def addFailure(self, test, err):
        Result.addFailure(self, test, err)
        self.failures.append((test,
                              self._exc_info_to_string(err, test) + self.tbinfo,
                              self.capt))
        self.writeRes('FAIL','F')
        
    def addSkip(self, test):
        Result.addSkip(self, test)
        self.skip.append((test, '', ''))
        self.writeRes('SKIP','S')

    def addSuccess(self, test):
        Result.addSuccess(self, test)
        self.writeRes('ok', '.')
        
    def printErrors(self):
        log.debug('printErrors called')
        _TextTestResult.printErrors(self)
        self.printErrorList('DEPRECATED', self.deprecated)
        self.printErrorList('SKIPPED', self.skip)
        log.debug('calling plugin reports')
        call_plugins(self.conf.plugins, 'report', self.stream)
        
    def printErrorList(self, flavor, errors):
        for test, err, capt in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavor,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)
            if capt is not None and len(capt):
                self.stream.writeln(ln('>> begin captured stdout <<'))
                self.stream.writeln(capt)
                self.stream.writeln(ln('>> end captured stdout <<'))

    def startTest(self, test):
        Result.startTest(self, test)
        if not isinstance(test, TestSuite):
            _TextTestResult.startTest(self, test)
        
    def stopTest(self, test):
        Result.stopTest(self, test)
        if not isinstance(test, TestSuite):
            _TextTestResult.stopTest(self, test)
                
    def writeRes(self, long, short):
        if self.showAll:
            self.stream.writeln(long)
        else:
            self.stream.write(short)

    def _exc_info_to_string(self, err, test):
        try:
            return _TextTestResult._exc_info_to_string(self, err, test)
        except TypeError:
            # 2.3: does not take test arg
            return _TextTestResult._exc_info_to_string(self, err)

        
def start_capture():
    """Start capturing output to stdout. DOES NOT reset the buffer.
    """
    log.debug('start capture from %r' % sys.stdout)
    stdout.append(sys.stdout)
    sys.stdout = StringIO()
    log.debug('sys.stdout is now %r' % sys.stdout)

def end_capture():
    """Stop capturing output to stdout. DOES NOT reset the buffer.x
    """
    if stdout:
        sys.stdout = stdout.pop()
        log.debug('capture ended, sys.stdout is now %r' % sys.stdout)
        
    
def ln(label):
    label_len = len(label) + 2
    chunk = (70 - label_len) / 2
    out = '%s %s %s' % ('-' * chunk, label, '-' * chunk)
    pad = 70 - len(out)
    if pad > 0:
        out = out + ('-' * pad)
    return out

