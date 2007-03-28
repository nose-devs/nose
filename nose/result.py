"""Test result handlers. Base class (Result) implements plugin handling,
output capture, and assert introspection, and handles deprecated and skipped
tests. TextTestResult is a drop-in replacement for unittest._TextTestResult
that uses the capabilities in Result.
"""

import logging
from unittest import _TextTestResult
from nose.config import Config


log = logging.getLogger('nose.result')


class TextTestResult(_TextTestResult):
    """Text test result that extends unittest's default test result
    support for a configurable set of errorClasses (eg, Skip,
    Deprecated, TODO) that extend the errors/failures/success triad.
    """    
    def __init__(self, stream, descriptions, verbosity, config=None,
                 errorClasses=None):
        if errorClasses is None:
            errorClasses = {}
        self.errorClasses = errorClasses
        if config is None:
            config = Config()       
        self.config = config
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
                
    def addError(self, test, err):
        """Overrides normal addError to add support for
        errorClasses. If the exception is a registered class, the
        error will be added to the list for that class, not errors.
        """
        ec, ev, tb = err
        handler, label, isfail = self.errorClasses.get(ec, (None, None, None))
        if not handler:
            return self._addError(test, err)
        errlist = getattr(self, handler, None)
        if errlist is None:
            warn("No attribute %s: needed to handle errors "
                 "of class %s" % (handler, ec), RuntimeWarning)
            return self._addError(test, err)
        errlist.append((test, self._exc_info_to_string(err, test)))
        # Might get patched into a streamless result
        stream = getattr(self, 'stream', None)
        if stream is not None:
            if self.showAll:
                self.stream.write(label)
            elif self.dots:
                self.stream.write(label[:1])

    def printErrors(self):
        """Overrides to print all errorClasses errors as well.
        """
        _TextTestResult.printErrors(self)
        for cls in self.errorClasses.keys():
            handler, label, isfail = self.errorClasses[cls]
            self.printErrorList(label, getattr(self, handler, []))

    def wasSuccessful(self):
        """Overrides to check that there are no errors in errorClasses
        lists that are marked as errors that should cause a run to
        fail.
        """
        if self.errors or self.failures:
            return False
        for cls in self.errorClasses.keys():
            handler, label, isfail = self.errorClasses[cls]
            if not isfail:
                continue
            if getattr(self, handler, []):
                return False
        return True

    def _addError(self, test, err):
        self.errors.append((test, self._exc_info_to_string(err, test)))

    def _exc_info_to_string(self, err, test):
        try:
            return _TextTestResult._exc_info_to_string(self, err, test)
        except TypeError:
            # 2.3: does not take test arg
            return _TextTestResult._exc_info_to_string(self, err)

        
        
    

