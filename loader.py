import os
import unittest
from inspect import isclass, isfunction
from nose.case import FunctionTestCase
from nose.fixture import Context
from nose.selector import TestAddress
from nose.util import cmp_lineno, isgenerator
from suite import LazySuite, ContextSuiteFactory

class TestLoader(unittest.TestLoader):

    def __init__(self, context=None):
        # FIXME would get config too
        # FIXME would get workingdir too
        # FIXME would get selector too
        if context is None:
            context = Context()
        self.context = context
        self.suiteClass = ContextSuiteFactory(context)
        unittest.TestLoader.__init__(self)        

    def loadTestsFromDir(self, path):
        print "load from dir %s" % path
        for entry in os.listdir(path):
            print "at %s" % entry
            # FIXME package support here: always descend into packages
            entry_path = os.path.abspath(os.path.join(path, entry))
            if not entry.startswith('test'):
                continue
            if (os.path.isfile(entry_path)
                and entry.endswith('.py')):
                yield self.loadTestsFromName(entry)
            elif os.path.isdir(entry_path):
                yield self.loadTestsFromDir(entry)
        # FIXME give plugins a chance?

    def loadTestsFromFile(self, filename):
        # only called for non-module files
        # FIXME give plugins a chance
        pass

    def loadTestsFromModule(self, module):
        tests = []
        test_classes = []
        func_tests = []
        for item in dir(module):
            test = getattr(module, item, None)
            if isclass(test):
                # FIXME use a selector
                if (issubclass(test, unittest.TestCase)
                    or test.lower().startswith('test')):
                    test_classes.append(test)
            elif isfunction(test):
                # FIXME use selector
                # FIXME check for generators
                func_tests.append(test)
        func_tests.sort(cmp_lineno)
        tests.append(self.suiteClass(map(FunctionTestCase, func_tests)))
        # FIXME this won't pick up non unittest classes correctly
        # FIXME this won't pick up generators correctly
        tests.append(self.suiteClass(map(self.loadTestsFromTestCase,
                                         test_classes)))
        # FIXME give plugins a chance
        return self.suiteClass(tests)
                                               
    def loadTestsFromName(self, name, module=None):
        # FIXME would pass working dir too
        addr = TestAddress(name)
        print "load from %s (%s)" % (name, addr)
        # FIXME these are all valid only if module is None
        if addr.module:
            # FIXME use nose importer; obviously this won't
            # work for dotted names as written
            module = __import__(addr.module)
            return self.loadTestsFromModule(module)
        elif addr.filename:
            path = addr.filename
            if os.path.isdir(path):
                return LazySuite(lambda: self.loadTestsFromDir(path))
            elif os.path.isfile(path):
                return LazySuite(lambda: self.loadTestsFromFile(path))
        else:
            # just a function? what to do? I think it can only be
            # handled when module is not None
            pass
        # FIXME give plugins a chance?
                
    def loadTestsFromNames(self, names, module=None):
        def load():
            for test in self.loadTestsFromName(name, module):
                yield test
        return LazySuite(load)
