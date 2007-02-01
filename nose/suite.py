"""nose TestSuite subclasses that implement lazy test collection for modules,
classes and directories, and provide suite-level fixtures (setUp/tearDown
methods).
"""
from __future__ import generators

import logging
import sys
import unittest
from nose.case import MethodTestCase
from nose.config import Config
from nose.importer import _import
from nose.util import try_run

log = logging.getLogger('nose.suite')


class LazySuite(unittest.TestSuite):
    """Generator-based test suite. Pass a callable that returns an iterable of
    tests, and a nose.config.Config. Also provides hooks (setUp and tearDown)
    for suite-level fixtures.
    """
    # _exc_info_to_string needs this property
    failureException = unittest.TestCase.failureException
    
    def __init__(self, loadtests, conf=None):
        self._loadtests = loadtests
        if conf is None:
            conf = Config()
        self.conf = conf

    def __iter__(self):
        return iter(self._tests)
        
    def loadtests(self):
        for test in self._loadtests():
            yield test

    # lazy property so subclasses can override loadtests()
    _tests = property(lambda self: self.loadtests(),
                      None, None,
                      'Tests in this suite (iter)')

    def __call__(self, *arg, **kw):
        self.run(*arg, **kw)
        
    def run(self, result):
        result.startTest(self)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, sys.exc_info())
                return
            for test in self._tests:
                log.debug("running test %s", test)
                if result.shouldStop:
                    break
                test(result)
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, sys.exc_info())            
            return result
        finally:
            result.stopTest(self)
            
    def setUp(self):
        pass
        
    def shortDescription(self):
        return str(self) # FIXME
    
    def tearDown(self):
        pass


class GeneratorMethodTestSuite(LazySuite):
    """Test suite for test methods that are generators.
    """
    def __init__(self, cls, method):
        self.cls = cls
        self.method = method

    def loadtests(self):
        inst = self.cls()
        suite = getattr(inst, self.method)

        for test in suite():
            try:
                test_method, arg = (test[0], test[1:])
            except ValueError:
                test_method, arg = test[0], tuple()
            log.debug('test_method: %s, arg: %s', test_method, arg)
            case = None
            if callable(test_method):
                name = test_method.__name__
                case = test_method
            else:
                name = test_method
            yield MethodTestCase(
                self.cls, name, self.method, case, *arg)

            
class TestClass(LazySuite):
    """Lazy suite that collects tests from a class.
    """
    def __init__(self, loadtests, conf, cls):
        self.cls = cls
        LazySuite.__init__(self, loadtests, conf)

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'test class %s' % self.cls
        
    def loadtests(self):
        for test in self._loadtests(self.cls):
            yield test


class TestDir(LazySuite):
    """Lazy suite that collects tests from a directory.
    """
    def __init__(self, loadtests, conf, path, module=None, importPath=None):
        self.path = path
        self.module = module
        self.importPath = importPath
        LazySuite.__init__(self, loadtests, conf)

    def __repr__(self):
        return "test directory %s in %s" % (self.path, self.module)
    __str__ = __repr__
        
    def loadtests(self):
        for test in self._loadtests(self.path, self.module,
                                    self.importPath):
            yield test

            
class TestModule(LazySuite):
    """Lazy suite that collects tests from modules and packages.

    This suite collects module members that match the testMatch
    regular expression. For packages, it also collects any modules or
    packages found in the package __path__ that match testMatch. For
    modules that themselves do not match testMatch, the collector collects
    doctests instead of test functions.

    Before returning the first collected test, any defined setup method
    will be run. Packages may define setup, setUp, setup_package or
    setUpPackage, modules setup, setUp, setup_module, setupModule or
    setUpModule. Likewise, teardown will be run if defined and if setup
    ran successfully; teardown methods follow the same naming rules as
    setup methods.
    """
    fromDirectory = None
    
    def __init__(self, loadtests, conf, moduleName=None, path=None,
                 module=None):
        self.moduleName = moduleName
        self.path = path
        self.module = module
        if module and moduleName is None:
            self.moduleName = module.__name__        
        LazySuite.__init__(self, loadtests, conf)
        
    def __repr__(self):
        return "test module %s in %s" % (self.moduleName, self.path)
    __str__ = __repr__

    def loadtests(self):
        tests = self._loadtests(self.module, self.path)
        try:
            for test in tests:
                yield test
        except TypeError:
            # python 2.3: TestSuite not iterable
            for test in tests._tests:
                yield test

    def id(self):
        return self.__str__()
        
    def setUp(self):
        """Run any package or module setup function found. For packages, setup
        functions may be named 'setupPackage', 'setup_package', 'setUp',
        or 'setup'. For modules, setup functions may be named
        'setupModule', 'setup_module', 'setUp', or 'setup'. The setup
        function may optionally accept a single argument; in that case,
        the test package or module will be passed to the setup function.
        """
        log.debug('TestModule.setUp')
        if self.module is None:
            self.module = _import(self.moduleName, [self.path], self.conf)
            log.debug('Imported %s from %s on %s', self.module,
                      self.moduleName, self.path)
        if hasattr(self.module, '__path__'):
            names = ['setupPackage', 'setUpPackage', 'setup_package']
        else:
            names = ['setupModule', 'setUpModule', 'setup_module']
        names += ['setUp', 'setup']
        try_run(self.module, names)
            
    def tearDown(self):
        """Run any package or module teardown function found. For packages,
        teardown functions may be named 'teardownPackage',
        'teardown_package' or 'teardown'. For modules, teardown functions
        may be named 'teardownModule', 'teardown_module' or
        'teardown'. The teardown function may optionally accept a single
        argument; in that case, the test package or module will be passed
        to the teardown function.

        The teardown function will be run only if any package or module
        setup function completed successfully.
        """
        if hasattr(self.module, '__path__'):
            names = ['teardownPackage', 'teardown_package']
        else:
            names = ['teardownModule', 'teardown_module']
        names += ['tearDown', 'teardown']        
        try_run(self.module, names)
