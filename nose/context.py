import logging
import sys
from inspect import isclass, ismodule
from nose.config import Config
from nose.case import Test
from nose.util import resolve_name, try_run

log = logging.getLogger(__name__)

class FixtureContext(object):

    def __init__(self, config=None, result_proxy=None):
        """Initialize a FixtureContext for a test run.

        Optional arguments:
        
        * config: the configuration of this test run. If no config is passed,
          a default config will be used.
        
        * result_proxy: a callable that may be passed a result and test, and
          returns a proxy object that will mediate between the test wrapper
          and.
        """
        if config is None:
            config = Config()
        self.config = config
        self.result_proxy = result_proxy
        self.parents = {}
        self.tests = {}
        self.setup_fired = {}
        self.setup_ok = {}

    def __call__(self, test):
        # FIXME may be more efficient to pass the actual class?
        log.debug("Add context for test %s", test)
        if hasattr(test, 'cls'):
            cls, module = test.cls, test.cls.__module__
            parent = "%s.%s" % (module, cls.__name__)
        elif hasattr(test, 'test'):
            parent = test.test.__module__
        else:
            parent = test.__module__
        return self.add(parent, test)

    def add(self, parent, test):
        log.debug("Add %s to parent %s", test, parent)
        for part in self._parts(parent):
            self.tests.setdefault(part, []).append(test)
            self.parents.setdefault(test, []).append(part)
        return Test(self, test)

    def setup(self, test):
        """Context setup. If this is the first for any surrounding package or
        module or class of this test, fire the parent object setup; record
        that it was fired
        """
        log.debug("Context setup for %s", test)
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
        """Context teardown. If this is the last for an surrounding package
        or module, and setup fired for that module or package, fire teardown
        for the module/package/class too. otherwise pop off of the stack for
        thatmodule/package/class.
        """
        log.debug("Context teardown for %s", test)
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
