"""nose TestSuite subclasses that implement lazy test collection for modules,
classes and directories, and provide suite-level fixtures (setUp/tearDown
methods).
"""
import logging
import os
import sys
import unittest
from nose.case import MethodTestCase
from nose.config import Config
from nose.importer import load_source
from nose.util import try_run

log = logging.getLogger('nose.suite')

class StopTest(Exception):
    pass


class TestCollector(unittest.TestSuite):
    """A test suite with setup and teardown methods.
    """
    def __init__(self, loader=None, **kw):
        super(TestCollector, self).__init__(**kw)
        self.loader = loader
        self.conf = loader.conf
        self._collected = False

    def __nonzero__(self):
        self.collectTests()
        return bool(self._tests)

    def __len__(self):
        self.collectTests()
        return len(self._tests)

    def __iter__(self):
        self.collectTests()
        return iter(self._tests)
    
    def __call__(self, *arg, **kw):
        self.run(*arg, **kw)

    def id(self):
        return self.__str__()

    def collectTests(self):
        pass
        
    def run(self, result):
        self.startTest(result)
        try:
            self.collectTests()
            if not self:
                return
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except StopTest:
                pass
            except:
                result.addError(self, sys.exc_info())
                return
            for test in self:
                log.debug("running test %s", test)
                if result.shouldStop:
                    break
                test(result)
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except StopTest:
                pass
            except:
                result.addError(self, sys.exc_info())            
            return result
        finally:
            self.stopTest(result)
        
    def setUp(self):
        pass
        
    def shortDescription(self):
        return str(self) # FIXME

    def startTest(self):
        result.startTest(self)

    def stopTest(self):
        result.stopTest(self)
    
    def tearDown(self):
        pass

# backwards compatibility
TestSuite = TestCollector


class ModuleSuite(TestCollector):
    """Test Collector that collects tests in a single module or
    package. For pakages, tests are collected depth-first. This is to
    ensure that a module's setup and teardown fixtures are run only if
    the module contains tests.
    """
    def __init__(self, modulename=None, filename=None, working_dir=None,
                 testnames=None, **kw):
        self.modulename = modulename
        self.filename = filename
        self.working_dir = working_dir
        self.testnames = testnames
        self.module = None
        super(ModuleSuite, self).__init__(**kw)
        
    def __repr__(self):
        path = os.path.dirname(self.filename)
        while (os.path.exists(os.path.join(path, '__init__.py'))):
            path = os.path.dirname(path)
        return "test module %s in %s" % (self.modulename, path)
    __str__ = __repr__

    def addTest(self, test):
        # depth-first?
        if test:
            self._tests.append(test)

    def collectTests(self):
        # print "Collect Tests %s" % self
        if self._collected or self._tests:
            return
        self._collected = True
        self._tests = []
        if self.module is None:
            # FIXME
            # We know the exact source of each module so why not?
            # We still need to add the module's parent dir (up to the top
            # if it's a package) to sys.path first, though
            self.module = load_source(self.name, self.path, self.conf)
        for test in self.loader.loadTestsFromModule(self.module,
                                                    self.testnames):
            self.addTest(test)

    def setUp(self):
        """Run any package or module setup function found. For packages, setup
        functions may be named 'setupPackage', 'setup_package', 'setUp',
        or 'setup'. For modules, setup functions may be named
        'setupModule', 'setup_module', 'setUp', or 'setup'. The setup
        function may optionally accept a single argument; in that case,
        the test package or module will be passed to the setup function.
        """
        log.debug('TestModule.setUp')
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

# backwards compatibility
TestModule = ModuleSuite


class LazySuite(TestSuite):
    """Generator-based test suite. Pass a callable that returns an iterable of
    tests, and a nose.config.Config.
    """
    # _exc_info_to_string needs this property
    failureException = unittest.TestCase.failureException
    
    def __init__(self, loadtests, conf=None, **kw):
        self._loadtests = loadtests
        if conf is None:
            conf = Config()
        self.conf = conf

    def loadtests(self):
        for test in self._loadtests():
            yield test

    # lazy property so subclasses can override loadtests()
    _tests = property(lambda self: self.loadtests(),
                      None, None,
                      'Tests in this suite (iter)')


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
            if callable(test_method):
                name = test_method.__name__
            else:
                name = test_method
            yield MethodTestCase(self.cls, name, self.method, *arg)

            
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
