import unittest

class Context(object):

    def __init__(self):
        self.modules = {}
        self.tests = {}
        self.setup_fired = {}
        self.setup_ok = {}

    # FIXME this won't work unless there are tests in the top-level package
    # and each of the intermediary levels... the test has to be added and
    # has to reference every module up the chain, and be popped off of all
    # of those lists when it hits teardown
    def add(self, module, test):
        if isinstance(module, basestring):
            module = __import__(module)
        self.modules.setdefault(module, []).append(test)
        self.tests[test] = module
        return Case(self, test)

    def setup(self, test):
        # if this is the first for any surrounding package or module of
        # this test, fire the package and  module setup; record that it
        # was fired
        mod = self.tests.get(test)
        if not mod:
            # not my test?
            raise Exception("Module for test %s not found in context")
        if self.setup_fired.get(mod):
            return
        self.setup_fired[mod] = True
        if hasattr(mod, 'setup'):
            mod.setup(mod) # FIXME -- try all the names, etc
        self.setup_ok[mod] = True
            
    def teardown(self, test):
        # if this is the last for an surrounding package or module, and setup
        # fired for that module or package, fire teardown for the module
        # /package too. otherwise pop off of the stack for that module/
        # package
        mod = self.tests.get(test)
        if not mod:
            # not my test?
            raise Exception("Module for test %s not found in context")
        self.modules[mod].remove(test)
        if (not self.modules[mod] 
            and self.setup_ok.get(mod) 
            and hasattr(mod, 'teardown')):
            mod.teardown(mod)

            
class Case(unittest.TestCase):

    def __init__(self, context, test):
        print "Case %s %s" % (context, test)
        self.context = context
        self.test = test
        unittest.TestCase.__init__(self)
        
    def __call__(self, *arg, **kwarg):
        print "call %s %s %s" % (self, arg, kwarg)
        return self.run(*arg, **kwarg)

    def setUp(self):
        print "setup %s" % self
        self.context.setup(self.test)

    def run(self, result):
        self.result = result
        unittest.TestCase.run(self, result)
        
    def runTest(self):
        self.test(self.result)

    def tearDown(self):
        self.context.teardown(self.test)
