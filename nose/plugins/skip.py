import os
from nose.plugins.base import Plugin
from warnings import warn


class Skip(Plugin):
    """Plugin that installs a SKIP error class for the SkipTest
    exception.  When SkipTest is raised, the exception will be logged
    in the skipped attribute of the result, 'S' or 'SKIP' (verbose)
    will be output, and the exception will not be counted as an error
    or failure.
    """
    enabled = True

    def options(self, parser, env=os.environ):
        env_opt = 'NOSE_WITHOUT_SKIP'
        parser.add_option('--no-skip', action='store_true',
                          dest='noSkip', default=env.get(env_opt, False),
                          help="Disable special handling of SkipTest "
                          "exceptions.")

    def configure(self, options, conf):
        if not self.can_configure:
            return
        self.conf = conf
        disable = getattr(options, 'noSkip', False)
        if disable:
            self.enabled = False
    
    def prepareTestResult(self, result):
        if not hasattr(result, 'errorClasses'):
            self.patchResult(result)
        if SkipTest not in result.errorClasses:
            result.errorClasses[SkipTest] = ('skipped', 'SKIP', False)
            result.skipped = []
            
    def patchResult(self, result):
        result._orig_addError, result.addError = \
            result.addError, add_error_patch(result)
        result._orig_wasSuccessful, result.wasSuccessful = \
            result.wasSuccessful, wassuccessful_patch(result)
        if hasattr(result, 'printErrors'):
            result._orig_printErrors, result.printErrors = \
                result.printErrors, print_errors_patch(result)
        result.errorClasses = {}


class SkipTest(Exception):
    """Raise this exception to mark a test as skipped.
    """
    pass


def add_error_patch(result):
    """Create a new addError method to patch into a result instance
    that recognizes the errorClasses attribute and deals with
    errorclasses correctly.
    """
    self = result
    def addError(test, err):
        ec, ev, tb = err
        handler, label, isfail = self.errorClasses.get(ec, (None, None, None))
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
    return addError


def print_errors_patch(result):
    """Create a new printErrors method that prints errorClasses items
    as well.
    """
    self = result
    def printErrors():
        self._orig_printErrors()
        for cls in self.errorClasses.keys():
            handler, label, isfail = self.errorClasses[cls]
            self.printErrorList(label, getattr(self, handler, []))
    return printErrors


def wassuccessful_patch(result):
    """Create a new wasSuccessful method that checks errorClasses for
    exceptions that were put into other slots than error or failure
    but that still count as not success.
    """
    self = result
    def wasSuccessful():
        if self.errors or self.failures:
            return False
        for cls in self.errorClasses.keys():
            handler, label, isfail = self.errorClasses[cls]
            if not isfail:
                continue
            if getattr(self, handler, []):
                return False
        return True
    return wasSuccessful
