"""Discovery-based test loader.
"""
import logging
import os
import sys
import types
import unittest

from inspect import isfunction, ismethod
from nose.case import *
from nose.config import Config
from nose.importer import add_path, _import
from nose.plugins import call_plugins
from nose.selector import defaultSelector
from nose.suite import ModuleSuite, TestClass, TestDir, \
    GeneratorMethodTestSuite
from nose.util import isgenerator, split_test_name, try_run

log = logging.getLogger(__name__)

class LoaderException(Exception):
    pass
    
class TestLoader(unittest.TestLoader):
    """Default nose test loader. 

    Methods that shadow those in unittest.TestLoader are compatible with the
    usage in the base class. Others may be generators or interpret 'module' as
    the module prefix of the thing to be loaded, not the module to be
    examined, for example. Integrates closely with nose.selector.Selector to
    determine what is a test, and classes in nose.suite to defer loading as
    long as possible.
    """
    suiteClass = ModuleSuite
    
    def __init__(self, conf=None, selector=None):
        if conf is None:
            conf = Config()
        self.conf = conf
        if selector is None:
            selector = defaultSelector(conf)
        self.selector = selector
        self.plugins = self.conf.plugins
                
    def loadTestsFromDir(self, dirname, module=None, importPath=None):
        """Find tests in a directory.

        Each item in the directory is tested against self.selector, wantFile
        or wantDirectory as appropriate. Those that are wanted are returned.
        """
        log.info("%s load tests in %s [%s]", self, dirname, module)
        if dirname is None:
            return        
        if not os.path.isabs(dirname):
            raise ValueError("Dir paths must be specified as "
                             "absolute paths (%s)" % dirname)
        self.conf.working_dir = dirname
        if importPath is None:
            importPath = dirname
        
        # Ensure that any directory we examine is on sys.path
        if self.conf.addPaths:
            add_path(dirname)
            
        # to ensure that lib paths are set up correctly before tests are
        # run, examine directories that look like lib or module
        # directories first and tests last
        def test_last(a, b, m=self.conf.testMatch):
            if m.search(a) and not m.search(b):
                return 1
            elif m.search(b) and not m.search(a):
                return -1
            return cmp(a, b)
        
        entries = os.listdir(dirname)
        entries.sort(test_last)
        for item in entries:
            tests = None
            log.debug("candidate %s in %s", item, dirname)
            path = os.path.join(dirname, item)
            for test in self.loadTestsFromName(path,
                                               module=module,
                                               importPath=importPath):
                yield test
        
    def loadTestsFromModule(self, module=None, name=None,
                            package=None, importPath=None):
        """Load tests from module at (optional) import path. One of module or
        name must be supplied. If name is supplied, the module name (prepended
        with package if that is not empty) will be imported.
        """
        if module is None:
            if name is None:
                raise LoaderException("loadTestsFromModule: one of module or "
                                      "name must be supplied")
            if package is not None:
                modname = "%s.%s" % (package, name)
            else:
                modname = name
            try:
                log.debug("Importing %s from %s", modname, importPath)
                module = _import(modname, [importPath], self.conf)
            except KeyboardInterrupt:
                raise
            except:
                error = sys.exc_info()
                return self.suiteClass(tests=[], error=error)
        
        log.debug("load from module %s (%s)", module, importPath)
        tests = []
        if self.selector.wantModuleTests(module):
            log.debug("load tests from %s", module.__name__)
            for test in self.testsInModule(module, importPath):
                tests.append(test)
        # give plugins a chance
        for plug in self.conf.plugins:
            if hasattr(plug, 'loadTestsFromModule'):
                log.debug("collect tests in %s with plugin %s",
                          module.__name__, plug.name)
                for test in plug.loadTestsFromModule(module):
                    tests.append(test)
        # recurse into all modules
        if hasattr(module, '__path__') and module.__path__:
            path = module.__path__[0]
            # setting the module prefix means that we're
            # loading from our own parent directory, since we're
            # loading xxx.yyy, not just yyy, so ask the importer to
            # import from self.path (the path we were imported from),
            # not path (the path we're at now)
            tests.append(TestDir(self.loadTestsFromDir, self.conf, path,
                                 module.__name__, importPath))
        # compat w/unittest
        return self.suiteClass(tests, module=module)

    def loadTestsFromName(self, name, module=None, importPath=None):
        """Load tests from test name. Name may be a file, directory or
        module. Specify module (or module) as name to load from a
        particular module. Specify importPath to load
        from that path.
        """
        # compatibility shim
        try:
            module = module.__name__
        except AttributeError:
            pass

        if importPath is None:
            importPath = self.conf.working_dir
        
        tests = None
        path, mod_name, fn = split_test_name(name)
        log.debug('test name %s resolves to path %s, module %s, callable %s'
                  % (name, path, mod_name, fn))

        if path:
            if os.path.isfile(path):
                log.debug("%s is a file", path)
                if self.selector.wantFile(name, module):
                    tests = self.loadTestsFromPath(path,
                                                   module=module,
                                                   importPath=importPath)
            elif os.path.isdir(path):
                log.debug("%s is a directory", path)
                if self.selector.wantDirectory(path):
                    init = os.path.join(path, '__init__.py')
                    if os.path.exists(init):
                        tests = self.loadTestsFromPath(path,
                                                       module=module,
                                                       importPath=importPath)
                    else:
                        # dirs inside of modules don't belong to the
                        # module, so module and importPath are not passed
                        tests = self.loadTestsFromDir(path)
            else:
                # ignore non-file, non-path item
                log.warning("%s is neither file nor path", path)
        elif mod_name:
            # handle module-like names
            log.debug("%s is a module name", name)
            yield self.loadTestsFromModule(name=name,
                                           package=module,
                                           importPath=importPath)
        elif module:
            # handle func-like names in a module            
            raise ValueError("No module or file specified in test name")
        if tests:
            for test in tests:
                yield test
        # give plugins a chance
        for plug in self.plugins:
            if hasattr(plug, 'loadTestsFromName'):
                for test in plug.loadTestsFromName(name, module, importPath):
                    yield test

    def loadTestsFromNames(self, names=None, module=None):
        """Load tests from names. Behavior is compatible with unittest:
        if module is specified, all names are translated to be relative
        to that module; the tests are appended to conf.tests, and
        loadTestsFromModule() is called. Otherwise, the names are
        loaded one by one using loadTestsFromName.
        """
        if names is None:
            names = [ self.cwd() ]
        for name in names:
            yield self.loadTestsFromName(name, module)
            
#         def rel(name, mod):
#             if not name.startswith(':'):
#                 name = ':' + name
#             return "%s%s" % (mod, name)
        
#         if module:
#             log.debug("load tests from module %r" % module)
#             # configure system to load only requested tests from module
#             if names:
#                 self.conf.tests.extend([ rel(n, module.__name__)
#                                          for n in names ])
#             try:
#                 mpath = os.path.dirname(module.__path__[0])
#             except AttributeError:
#                 mpath = os.path.dirname(module.__file__)
                
#             return self.loadTestsFromModule(module, importPath=mpath)
#         else:
#             tests = []
#             for name in names:
#                 for test in self.loadTestsFromName(name):
#                     tests.append(test)
#         return self.suiteClass(tests)

    def loadTestsFromPath(self, path, module=None, importPath=None):
        """Load tests from file or directory at path.
        """
        head, test = os.path.split(path)
        if importPath is None:
            importPath = head
        
        log.debug("path %s is %s in %s", path, test, importPath)
        ispymod = True
        if os.path.isfile(path):
            if path.endswith('.py'):
                # trim the extension of python files
                test = test[:-3]
            else:
                ispymod = False
        elif not os.path.exists(os.path.join(path, '__init__.py')):
            ispymod = False
        if ispymod:
            yield self.loadTestsFromModule(name=test, package=module,
                                           importPath=importPath)
        # give plugins a chance
        for plug in self.plugins:
            if hasattr(plug, 'loadTestsFromPath'):
                for test in plug.loadTestsFromPath(path, module, importPath):
                    yield test
 
    def loadTestsFromTestCase(self, cls):
        log.debug("collect tests in class %s", cls)
        collected = self.testsInTestCase(cls)
        if self.sortTestMethodsUsing:
            collected.sort(self.sortTestMethodsUsing)        
        if issubclass(cls, unittest.TestCase):
            maketest = cls
        else:
            maketest = method_test_case(cls)
        return map(maketest, collected)
            
    def testsInModule(self, module, importPath=None):
        """Find functions and classes matching testMatch, as well as
        classes that descend from unittest.TestCase, return all found
        (properly wrapped) as tests.
        """
        
        entries = dir(module)
        tests = []
        func_tests = []
        for item in entries:
            log.debug("module candidate %s", item)
            test = getattr(module, item)
            if isinstance(test, (type, types.ClassType)):
                log.debug("candidate %s is a class", test)
                if self.selector.wantClass(test):
                    tests.append(TestClass(self.loadTestsFromTestCase,
                                           self.conf, test))
            elif isfunction(test):
                log.debug("candidate %s is a function", test)
                if not self.selector.wantFunction(test):
                    continue
                # might be a generator
                # FIXME LazySuite w/ generate...?
                if isgenerator(test):
                    log.debug("test %s is a generator", test)
                    func_tests.extend(self.generateTests(test))
                else:
                    # nope, simple functional test
                    func_tests.append(test)
        # run functional tests in the order in which they are defined
        func_tests.sort(cmp_line)
        tests.extend([ FunctionTestCase(test, fromDirectory=importPath)
                       for test in func_tests ])
        log.debug("Loaded tests %s from module %s", tests, module.__name__)
        return tests

    def testsInTestCase(self, cls):
        collected = []
        if cls in (object, type):
            return collected
        for item in dir(cls):
            attr = getattr(cls, item)
            log.debug("Check if selector wants %s (%s)", attr, cls)
            if ismethod(attr) and self.selector.wantMethod(attr):
                collected.append(item)                
        # base class methods; include those not overridden
        for base in cls.__bases__:
            basetests = self.testsInTestCase(base)
            for test in basetests:
                if not test in collected:
                    collected.append(test)
        return collected

    # FIXME this needs to be moved and generalized for methods?
    def generateTests(self, test):
        """Generate tests from a test function that is a generator.
        Returns list of test functions.
        """
        cases = []
        for expr in test():
            # build a closure to run the test, and give it a nice name
            def run(expr=expr):
                expr[0](*expr[1:])
            run.__module__ = test.__module__
            try:
                run.__name__ = '%s:%s' % (test.__name__, expr[1:])
            except TypeError:
                # can't set func name in python 2.3
                run.compat_func_name = '%s:%s' % (test.__name__, expr[1:])
                pass
            setup = ('setup', 'setUp', 'setUpFunc')
            teardown = ('teardown', 'tearDown', 'tearDownFunc')
            for name in setup:
                if hasattr(test, name):
                    setattr(run, name, getattr(test, name))
                    break
            for name in teardown:
                if hasattr(test, name):
                    setattr(run, name, getattr(test, name))
                    break
            cases.append(run)
        return cases
    
defaultTestLoader = TestLoader


def method_test_case(cls):
    """Return a method test case factory bound to cls.
    """
    def make_test_case(test_name):
        """Method test case factory. May return a method test case, or a
        generator method test suite, if the test case is a generator.
        """
        attr = getattr(cls, test_name)
        if isgenerator(attr):
            return GeneratorMethodTestSuite(cls, test_name)
        else:
            return MethodTestCase(cls, test_name)
    return make_test_case
