import os
import unittest
from nose.fixture import Context
from nose.selector import TestAddress
from suite import LazySuite, ContextSuiteFactory

class TestLoader(unittest.TestLoader):

    def __init__(self, context=None):
        # FIXME would get workingdir too
        # FIXME would get selector too? or can selector die?
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

    def loadTestsFromFile(self, filename):
        # only called for non-module files
        pass
                                               
    def loadTestsFromName(self, name, module=None):
        # FIXME would pass working dir too
        addr = TestAddress(name)
        print "load from %s (%s)" % (name, addr)
        # FIXME these are all valid only if module is None
        if addr.module:
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
                
    def loadTestsFromNames(self, names, module=None):
        def load():
            for test in self.loadTestsFromName(name, module):
                yield test
        return LazySuite(load)
