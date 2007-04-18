"""Test result handlers. Base class (Result) implements plugin handling,
output capture, and assert introspection, and handles deprecated and skipped
tests. TextTestResult is a drop-in replacement for unittest._TextTestResult
that uses the capabilities in Result.
"""

import logging
from unittest import _TextTestResult
from nose.config import Config
from nose.util import ln as _ln # backwards compat

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
        stream = getattr(self, 'stream', None)
        ec, ev, tb = err
        for cls, (storage, label, isfail) in self.errorClasses.items():
            if issubclass(ec, cls):
                storage.append((test, self._exc_info_to_string(err, test)))
                # Might get patched into a streamless result
                if stream is not None:
                    if self.showAll:
                        stream.writeln(label)
                    elif self.dots:
                        stream.write(label[:1])
                return
        self.errors.append((test, self._exc_info_to_string(err, test)))
        if stream is not None:
            if self.showAll:
                self.stream.writeln('ERROR')
            elif self.dots:
                stream.write('E')

    def printErrors(self):
        """Overrides to print all errorClasses errors as well.
        """
        _TextTestResult.printErrors(self)
        for cls in self.errorClasses.keys():
            storage, label, isfail = self.errorClasses[cls]
            self.printErrorList(label, storage)
        # Might get patched into a result with no config
        if hasattr(self, 'config'):
            self.config.plugins.report(self.stream)

    def wasSuccessful(self):
        """Overrides to check that there are no errors in errorClasses
        lists that are marked as errors that should cause a run to
        fail.
        """
        if self.errors or self.failures:
            return False
        for cls in self.errorClasses.keys():
            storage, label, isfail = self.errorClasses[cls]
            if not isfail:
                continue
            if storage:
                return False
        return True

    def _addError(self, test, err):
        self.errors.append((test, self._exc_info_to_string(err, test)))
        if self.showAll:
            self.stream.write('ERROR')
        elif self.dots:
            stream.write('E')

    def _exc_info_to_string(self, err, test):
        try:
            return _TextTestResult._exc_info_to_string(self, err, test)
        except TypeError:
            # 2.3: does not take test arg
            return _TextTestResult._exc_info_to_string(self, err)


def ln(*arg, **kw):
    from warnings import warn
    warn("ln() has moved to nose.util from nose.result and will be removed "
         "from nose.result in a future release. Please update your imports ",
         DeprecationWarning)
    return _ln(*arg, **kw)
    

