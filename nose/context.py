"""
Test Context
------------

The test context is responsible for wrapping test cases in the test
wrapper (nose.case.Test by default), and tracking the parent of any
given suite of tests, so that parent fixtures may be executed around
those tests. It also provides a passthrough for keyword arguments that
should be passed to each nose.case.Test (or other wrapper) as it is
instantiated.
"""
import logging
import sys
from inspect import isclass, ismodule
from nose.config import Config
from nose.case import Test
from nose.util import resolve_name, try_run

log = logging.getLogger(__name__)

class FixtureContext(object):

    def __init__(self, parent=None, config=None, **kw):
        """Initialize a FixtureContext for a test run.

        Optional arguments:

        * parent: the `parent` of the context, that is, the module or
          class to which tests in this context belong. Fixtures on the
          parent may be executed by calling the `setup()` and
          `teardown()` methods of this object.
        
        * config: the configuration of this test run. If no config is passed,
          a default config will be used.
        
        * `**kw`: any other keyword arguments will be passed to each
        nose.case.Tst test wrapper as it is instantiated.
        
        """
        self.parent = parent
        if config is None:
            config = Config()
        self.config = config
        self.test_kw = kw
        self.was_setup = False
        self.was_torndown = False

    def __call__(self, test):
        return self.add(test)

    def add(self, test):
        """Add the test to this context. Returns a nose.case.Test wrapping the
        test case. Override this method to use a different test wrapper.
        """
        log.debug("Add %s to parent %s", test, self.parent)
        return Test(self, test, **self.test_kw)

    def setup(self):
        """Context setup. Execute the setup method of the
        parent object, if it exists.
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
        """Context teardown. Execute the teardown method of the
        parent, if it exists.
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
