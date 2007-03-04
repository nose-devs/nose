import sys
from inspect import isclass, ismodule
from nose.case import Test
from nose.util import resolve_name, try_run

# FIXME support class-level fixtures here too (setup_class, teardown_class)
# possibly change terminology from module to more generic 'parent'?
class FixtureContext(object):

    def __init__(self, result_proxy=None):
        self.result_proxy = result_proxy
        self.parents = {}
        self.tests = {}
        self.setup_fired = {}
        self.setup_ok = {}
        
    def __call__(self, test):
        # FIXME may be more efficient to pass the actual class?
        # FIXME this doesn't work for classes that are not
        # defined at module top level
        print "Add context for test %s" % test
        if hasattr(test, 'cls'):
            cls, module = test.cls, test.cls.__module__
            parent = "%s.%s" % (module, cls.__name__)
        elif hasattr(test, 'test'):
            parent = test.test.__module__
        else:
            parent = test.__module__
        return self.add(parent, test)

    def add(self, parent, test):
        for part in self._parts(parent):           
            self.tests.setdefault(part, []).append(test)
            self.parents.setdefault(test, []).append(part)
        return Test(self, test)

    def setup(self, test):
        # if this is the first for any surrounding package or module of
        # this test, fire the package and  module setup; record that it
        # was fired
        for obj in self.parents.get(test):
            if self.setup_fired.get(obj):
                continue
            self.setup_fired[obj] = True
            if isclass(obj):
                names = ('setup_class',)
            else:
                names = ('setup_module', 'setup')
            # FIXME packages, camelCase
            try_run(obj, names)
            self.setup_ok[obj] = True
            
    def teardown(self, test):
        # if this is the last for an surrounding package or module, and setup
        # fired for that module or package, fire teardown for the module
        # /package too. otherwise pop off of the stack for that module/
        # package
        for obj in self.parents.get(test):
            self.tests[obj].remove(test)
            if (not self.tests[obj]
                and self.setup_ok.get(obj)):
                if isclass(obj):
                    names = ('teardown_class',)
                else:
                    names = ('teardown_module', 'teardown')
                # FIXME packages, camelCase
                try_run(obj, names)

    def _parts(self, parent):
        # FIXME assumes parent is a module
        try:
            if hasattr(parent, '__module__'):
                parent_name = "%s.%s" % (parent.__module__,  parent.__name__)
            else:
                parent_name = parent.__name__
        except AttributeError:
            parent_name, parent = parent, resolve_name(parent)
        name = []
        parts = []
        for part in parent_name.split('.'):
            name.append(part)
            part_name = '.'.join(name)
            if part_name == parent_name:
                parts.append(parent)
            else:            
                parts.append(resolve_name('.'.join(name)))
        # We want the parent parts in order from most to least
        # specific (foo.bar before foo)
        parts.reverse()
        return parts
