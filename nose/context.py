import logging
import sys
from inspect import isclass, ismodule
from nose.config import Config
from nose.case import Test
from nose.util import resolve_name, try_run

log = logging.getLogger(__name__)

class FixtureContext(object):

    def __init__(self, parent=None, config=None, result_proxy = None):
        """Initialize a FixtureContext for a test run.

        Optional arguments:
        
        * config: the configuration of this test run. If no config is passed,
          a default config will be used.
        
        * result_proxy: a callable that may be passed a result and test, and
          returns a proxy object that will mediate between the test wrapper
          and.
        """
        self.parent = parent
        if config is None:
            config = Config()
        self.config = config
        self.result_proxy = result_proxy
        self.was_setup = False
        self.was_torndown = False

    def __call__(self, test):
        # FIXME may be more efficient to pass the actual class?
        return self.add(test)

    def add(self, test):
        log.debug("Add %s to parent %s", test, self.parent)
        return Test(self, test, result_proxy=self.result_proxy)

    def setup(self):
        """Context setup. If this is the first for any surrounding package or
        module or class of this test, fire the parent object setup; record
        that it was fired
        """
        log.debug('context setup')
        if self.was_setup:
            return
        parent = self.parent
        if parent is None:
            return
        if isclass(parent):
            names = ('setup_class',)
        else:
            names = ('setup_module', 'setup')
        # FIXME packages, camelCase
        try_run(parent, names)
        self.was_setup = True
            
    def teardown(self):
        """Context teardown. If this is the last for an surrounding package
        or module, and setup fired for that module or package, fire teardown
        for the module/package/class too. otherwise pop off of the stack for
        thatmodule/package/class.
        """
        log.debug('context teardown')
        if not self.was_setup or self.was_torndown:
            return
        parent = self.parent
        if parent is None:
            return
        if isclass(parent):
            names = ('teardown_class',)
        else:
            names = ('teardown_module', 'teardown')
        # FIXME packages, camelCase
        try_run(parent, names)
        self.was_torndown = True
