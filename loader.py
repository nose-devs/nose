import os
import unittest
from inspect import isclass, isfunction, ismethod
from nose.case import FunctionTestCase
from nose.fixture import Context
from nose.selector import TestAddress
from nose.util import cmp_lineno, getpackage, isgenerator, ispackage
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

        # FIXME push dir onto sys.path
        for entry in os.listdir(path):
            if entry.startswith('.') or entry.startswith('_'):
                continue
            print "at %s" % entry
            # FIXME package support here: always descend into packages
            entry_path = os.path.abspath(os.path.join(path, entry))
            is_test = entry.startswith('test')
            is_file = os.path.isfile(entry_path)
            if is_file:
                is_dir = False
            else:
                is_dir = os.path.isdir(entry_path)
            is_package = ispackage(entry_path)
            if is_test and is_file and entry.endswith('.py'):
                yield self.loadTestsFromName(entry)
            elif is_dir:
                if is_package:
                    # Load the entry as a package: given the full path,
                    # loadTestsFromName() will figure it out
                    yield self.loadTestsFromName(getpackage(entry_path))
                elif is_test:
                    # Another test dir in this one: recurse lazily
                    yield LazySuite(
                        lambda: self.loadTestsFromDir(entry_path))
        # FIXME pop dir off of sys.path -- ideally, but we can't have
        # try: finally: around a generator and we can't guarantee that
        # a generator will be called often enough to do the pop
        
        # FIXME give plugins a chance?

    def loadTestsFromFile(self, filename):
        # only called for non-module files
        # FIXME give plugins a chance
        pass

    def loadTestsFromModule(self, module):
        print "Load from module %s" % module.__name__
        tests = []
        test_classes = []
        func_tests = []
        for item in dir(module):
            test = getattr(module, item, None)
            print "Check %s (%s) in %s" % (item, test, module.__name__)
            if isclass(test):
                # FIXME use a selector
                if (issubclass(test, unittest.TestCase)
                    or test.lower().startswith('test')):
                    test_classes.append(test)
            elif isfunction(test):
                # FIXME use selector
                func_tests.append(test)
        func_tests.sort(cmp_lineno)
        if func_tests:
            # FIXME check for generators
            tests.append(self.suiteClass(map(FunctionTestCase, func_tests)))
        if test_classes:
            # FIXME this won't pick up non unittest classes correctly
            # FIXME this won't pick up generators correctly
            tests.append(self.suiteClass(map(self.loadTestsFromTestCase,
                                             test_classes)))
        # Now, descend into packages
        # FIXME except this causes infinite recursion...
        paths = getattr(module, '__path__', [])
        for path in paths:
            # FIXME this isn't right... loading from packages is different
            # isn't it? or does loadTestsFromName squish the differences?
            tests.extend(self.loadTestsFromDir(path))
        # FIXME give plugins a chance
        return self.suiteClass(tests)
                                               
    def loadTestsFromName(self, name, module=None):
        # FIXME would pass working dir too
        addr = TestAddress(name)
        print "load from %s (%s) (%s)" % (name, addr, module)
        print addr.filename, addr.module, addr.call
        
        if module:
            # the name has been split, so if we got a full callable name
            # only, the split will be wrong, and we want the full name. If
            # we got a bucket:callable name, we only want the part after
            # the :
            if addr.call:
                name = addr.call
            obj = module
            parts = name.split('.')
            for part in parts:
                parent, obj = obj, getattr(obj, part, None)
            if obj is None:
                # no such test
                raise ValueError("No such test %s" % name)
            else:
                # load tests from the object, whether it's a class,
                # method or function
                # FIXME generator support -- this is going to recapitulate
                # a lot in load tests from module, it should be abstracted
                if isclass(obj):
                    return self.loadTestsFromTestCase(obj)
                elif ismethod(obj):
                    test = parent(obj.__name__)
                elif isfunction(obj):
                    test = obj
                else:
                    # give plugins a chance
                    raise ValueError("%s is not a function or method",
                                     obj)
                return self.suiteClass([obj])
        else:
            if addr.module:
                # FIXME use nose importer; obviously this won't
                # work for dotted names as written; plus it needs to do the
                # import only from the parent dir, and handle sys.modules
                module = __import__(addr.module)
                if addr.call:
                    return self.loadTestsFromName(addr.call, module)
                else:
                    return self.loadTestsFromModule(module)
            elif addr.filename:
                path = addr.filename
                if addr.call:
                    # FIXME need to filter the returned tests
                    raise Exception("Need to filter the returned tests")
                else:
                    if os.path.isdir(path):
                        # In this case we *can* be lazy since we know
                        # that each module in the dir will be fully
                        # loaded before its tests are executed; we
                        # also know that we're not going to be asked
                        # to load from . and ./some_module.py *as part
                        # of this named test load*
                        return LazySuite(
                            lambda: self.loadTestsFromDir(path))
                    elif os.path.isfile(path):
                        return self.loadTestsFromFile(path)
            else:
                # just a function? what to do? I think it can only be
                # handled when module is not None
                raise Exception("Bare function test name!")
        # FIXME give plugins a chance?
                
#     def loadTestsFromNames(self, names, module=None):
#         def load():
#             # FIXME this can break the fixture context
#             # say we get 2 names : foo:bar and foo:baz
#             # foo:bar will execute before foo:baz is loaded
#             # so foo:baz will not be run in the correct context
#             # this suggests that discovery has to proceed through
#             # *all* names before tests can start running
#             for test in self.loadTestsFromName(name, module):
#                 yield test
#         return LazySuite(load)
