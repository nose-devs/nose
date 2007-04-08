from new import instancemethod
from nose.plugins.base import Plugin
from nose.result import TextTestResult
from nose.util import odict



class MetaErrorClass(type):
    def __init__(self, name, bases, attr):
        errorClasses = []
        for name, detail in attr.items():
            if isinstance(detail, ErrorClass):
                attr.pop(name)
                for cls in detail:
                    errorClasses.append(
                        (cls, (name, detail.label, detail.isfailure)))
        super(MetaErrorClass, self).__init__(name, bases, attr)
        self.errorClasses = tuple(errorClasses)


class ErrorClass(object):
    def __init__(self, *errorClasses, **kw):
        self.errorClasses = errorClasses
        try:
            self.label = kw.pop('label')
            self.isfailure = kw.pop('isfailure')
        except KeyError, e:
            raise TypeError("%s is a required named argument for ErrorClass"
                            % e)

    def __iter__(self):
        return iter(self.errorClasses)


class ErrorClassPlugin(Plugin):
    __metaclass__ = MetaErrorClass
    score = 100
    errorClasses = ()

    def addError(self, test, err):
        err_cls, a, b = err
        classes = [e[0] for e in self.errorClasses]
        if filter(lambda c: issubclass(err_cls, c), classes):
            return True

    def prepareTestResult(self, result):
        if not hasattr(result, 'errorClasses'):
            self.patchResult(result)
        for cls, (storage_attr, label, isfail) in self.errorClasses:
            if cls not in result.errorClasses:
                storage = getattr(result, storage_attr, [])
                setattr(result, storage_attr, storage)
                result.errorClasses[cls] = (storage, label, isfail)

    def patchResult(self, result):
        result._orig_addError, result.addError = \
            result.addError, add_error_patch(result)
        result._orig_wasSuccessful, result.wasSuccessful = \
            result.wasSuccessful, wassuccessful_patch(result)
        if hasattr(result, 'printErrors'):
            result._orig_printErrors, result.printErrors = \
                result.printErrors, print_errors_patch(result)
        result.errorClasses = {}


def add_error_patch(result):
    """Create a new addError method to patch into a result instance
    that recognizes the errorClasses attribute and deals with
    errorclasses correctly.
    """
    return instancemethod(
        TextTestResult.addError.im_func, result, result.__class__)


def print_errors_patch(result):
    """Create a new printErrors method that prints errorClasses items
    as well.
    """
    return instancemethod(
        TextTestResult.printErrors.im_func, result, result.__class__)


def wassuccessful_patch(result):
    """Create a new wasSuccessful method that checks errorClasses for
    exceptions that were put into other slots than error or failure
    but that still count as not success.
    """
    return instancemethod(
        TextTestResult.wasSuccessful.im_func, result, result.__class__)

    
