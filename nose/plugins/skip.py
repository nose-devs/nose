from nose.plugins.base import Plugin
from warnings import warn

class Skip(Plugin):
    def prepareTestResult(self, result):
        if not hasattr(result, '_orig_addError'):
            self.patchResult(result)
        if SkipTest not in result.errorClasses:
            result.errorClasses[SkipTest] = ('skipped', 'SKIP')
            result.skipped = []
            
    def patchResult(self, result):
        result._orig_addError, result.addError = \
            result.addError, add_error_patch(result)
        if hasattr(result, 'printErrors'):
            result._orig_printErrors, result.printErrors = \
                result.printErrors, print_errors_patch(result)
        result.errorClasses = {}


class SkipTest(Exception):
    """Raise this exception to mark a test as skipped.
    """
    pass


def add_error_patch(result):
    self = result
    def add_error(test, err):
        ec, ev, tb = err
        handler, label = self.errorClasses.get(ec, (None, None))
        if not handler:
            return self._orig_addError(test, err)
        errlist = getattr(self, handler, None)
        if errlist is None:
            warn("No attribute %s in TestResult: needed to handle errors "
                 "of class %s" % (handler, ec), RuntimeWarning)
            return self._orig_addError(test, err)
        errlist.append((test, self._exc_info_to_string(err, test)))
        stream = getattr(self, 'stream', None)
        if stream is not None:
            if self.showAll:
                self.stream.write(label)
            elif self.dots:
                self.stream.write(label[:1])
    return add_error


def print_errors_patch(result):
    self = result
    def print_errors():
        self._orig_printErrors()
        for cls in self.errorClasses.keys():
            handler, label = self.errorClasses[cls]
            self.printErrorList(label, getattr(self, handler, []))
    return print_errors
