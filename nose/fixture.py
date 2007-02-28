import sys
from nose.case import Test

# FIXME support class-level fixtures here too (setup_class, teardown_class)
# possibly change terminology from module to more generic 'parent'?
class Context(object):

    def __init__(self):
        self.modules = {}
        self.tests = {}
        self.setup_fired = {}
        self.setup_ok = {}

    def __call__(self, test):
        return self.add(test.__module__, test)

    def add(self, module, test):
        for part in self._parts(module):           
            self.tests.setdefault(part, []).append(test)
            self.modules.setdefault(test, []).append(part)
        return Test(self, test)

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
                and hasattr(mod, 'teardown')): # FIXME other func names
                mod.teardown(mod)

    def _find_module(self, name):
        try:
            return sys.modules[name]
        except KeyError:
            print "--> Context import %s" % name
            mod = __import__(name)
            components = name.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

    def _parts(self, module):
        try:
            module_name = module.__name__
        except AttributeError:
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
