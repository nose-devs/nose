import sys
import unittest


class Context(object):

    def __init__(self):
        # FIXME the names modules and tests are reversed
        # modules is a list of tests per module and tests is
        # a list of modules per test
        self.modules = {}
        self.tests = {}
        self.setup_fired = {}
        self.setup_ok = {}

    # FIXME this won't work unless there are tests in the top-level package
    # and each of the intermediary levels... the test has to be added and
    # has to reference every module up the chain, and be popped off of all
    # of those lists when it hits teardown
    def add(self, module, test):
        for part in self._parts(module):           
            self.tests.setdefault(part, []).append(test)
            self.modules.setdefault(test, []).append(part)
        return Case(self, test)

    def setup(self, test):
        # if this is the first for any surrounding package or module of
        # this test, fire the package and  module setup; record that it
        # was fired
        for mod in self.modules.get(test):
            if self.setup_fired.get(mod):
                continue
            self.setup_fired[mod] = True
            if hasattr(mod, 'setup'):
                mod.setup(mod) # FIXME -- try all the names, etc
            self.setup_ok[mod] = True
            
    def teardown(self, test):
        # if this is the last for an surrounding package or module, and setup
        # fired for that module or package, fire teardown for the module
        # /package too. otherwise pop off of the stack for that module/
        # package
        for mod in self.modules.get(test):
            self.tests[mod].remove(test)
            if (not self.tests[mod] 
                and self.setup_ok.get(mod) 
                and hasattr(mod, 'teardown')):
                mod.teardown(mod)

    def _find_module(self, name):
        try:
            return sys.modules[name]
        except KeyError:
            mod = __import__(name)
            components = name.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

    def _parts(self, module):
        try:
            module_name = module.__name__
        except AttributeError:
            # FIXME won't work for dotteds
            module_name, module = module, self._find_module(module)
        name = []
        parts = []
        for part in module_name.split('.'):
            name.append(part)
            part_name = '.'.join(name)
            if part_name == module_name:
                parts.append(module)
            else:
                parts.append(self._find_module('.'.join(name)))
        # We want the module parts in order from most to least
        # specific (foo.bar before foo)
        parts.reverse()
        return parts


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
