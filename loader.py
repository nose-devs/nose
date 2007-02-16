import os
import sys
import unittest
from inspect import isclass, isfunction, ismethod
from nose.case import Failure, FunctionTestCase
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
        test_funcs = []
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
                test_funcs.append(test)
        test_classes.sort(lambda a, b: cmp(a.__name__, b.__name__))
        test_funcs.sort(cmp_lineno)
        tests = map(self.makeSuite, test_classes + test_funcs)

        # Now, descend into packages
        paths = getattr(module, '__path__', [])
        for path in paths:
            tests.extend(self.loadTestsFromDir(path))
        # FIXME give plugins a chance
        return self.suiteClass(tests)
    
    def loadTestsFromName(self, name, module=None):
        # FIXME refactor this method into little bites
        # FIXME would pass working dir too
        addr = TestAddress(name)
        print "load from %s (%s) (%s)" % (name, addr, module)
        print addr.filename, addr.module, addr.call
        
        if module:
            # Two cases:
            #  name is class.foo
            #    The addr will be incorrect, since it thinks class.foo is
            #    a dotted module name. It's actually a dotted attribute
            #    name. In this case we want to use the full submitted
            #    name as the name to load from the module.
            #  name is module:class.foo
            #    The addr will be correct. The part we want is the part after
            #    the :, which is in addr.call.
            if addr.call:
                name = addr.call
            parent, obj = self.resolve(name, module)
            return self.makeSuite(obj, parent)
        else:
            if addr.module:
                # FIXME use nose importer; obviously this won't
                # work for dotted names as written; plus it needs to do the
                # import only from the parent dir, and handle sys.modules
                try:
                    module = __import__(addr.module)
                except KeyboardInterrupt, SystemExit:
                    raise
                except:
                    exc = sys.exc_info()
                    return self.makeSuite(Failure(*exc))
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
                return self.makeSuite(
                    Failure(ValueError, "Unresolvable test name %s" % name))
        # FIXME give plugins a chance?

    def makeSuite(self, obj, parent=None):
        suite = self.suiteClass
        if isinstance(obj, unittest.TestCase):
            return suite([obj])
        elif isclass(obj):
            return self.loadTestsFromTestCase(obj)
        elif ismethod(obj):
            # FIXME Generators
            return suite([parent(obj.__name__)])
        elif isfunction(obj):
            # FIXME Generators
            return suite([FunctionTestCase(obj)])
        else:
            # FIXME give plugins a chance
            return suite(
                [Failure(ValueError,
                         "%s is not a function or method" % obj)])

    def resolve(self, name, module):
        obj = module
        parts = name.split('.')
        for part in parts:
            parent, obj = obj, getattr(obj, part, None)
        if obj is None:
            # no such test
            obj = Failure(ValueError, "No such test %s" % name)
        return parent, obj

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
