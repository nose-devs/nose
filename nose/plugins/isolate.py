"""Use the isolation plugin with --with-isolation or the
NOSE_WITH_ISOLATION environment variable to clean sys.modules after
each test module is loaded and executed.

The isolation module is in effect similar to wrapping the following
functions around the import and execution of each test module::

    def setup(module):
        module._mods = sys.modules.copy()
    
    def teardown(module):
        to_del = [ m for m in sys.modules.keys() if m not in
                   module._mods ]
        for mod in to_del:
            del sys.modules[mod]
        sys.modules.update(module._mods)

Isolation works only during lazy loading. In normal use, this is only
during discovery of modules within a directory, where the process of
importing, loading tests and running tests from each module is
encapsulated in a single loadTestsFromName call. This plugin
implements loadTestsFromNames to force the same lazy-loading there,
which allows isolation to work in directed mode as well as discovery,
at the cost of some efficiency: lazy-loading names forces full context
setup and teardown to run for each name, defeating the grouping that
is normally used to ensure that context setup and teardown are run the
fewest possible times for a given set of names.

PLEASE NOTE that this plugin should not be used in conjunction with
other plugins that assume that modules once imported will stay
imported; for instance, it may cause very odd results when used with
the coverage plugin.
"""

import logging
import sys

from nose.plugins import Plugin
from nose.suite import TestModule

log = logging.getLogger('nose.plugins.isolation')

class IsolationPlugin(Plugin):
    """
    Activate the isolation plugin to isolate changes to external
    modules to a single test module or package. The isolation plugin
    resets the contents of sys.modules after each test module or
    package runs to its state before the test. PLEASE NOTE that this
    plugin may not be used with the coverage plugin.
    """
    score = 10 # I want to be last
    name = 'isolation'

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self._mod_stack = []

    def beforeContext(self):
        """Copy sys.modules onto my mod stack
        """
        mods = sys.modules.copy()
        self._mod_stack.append(mods)

    def afterContext(self):
        """Pop my mod stack and restore sys.modules to the state
        it was in when mod stack was pushed.
        """
        mods = self._mod_stack.pop()
        to_del = [ m for m in sys.modules.keys() if m not in mods ]
        if to_del:
            log.debug('removing sys modules entries: %s', to_del)
            for mod in to_del:
                del sys.modules[mod]
        sys.modules.update(mods)

    def loadTestsFromNames(self, names, module=None):
        """Create a lazy suite that calls beforeContext and afterContext
        around each name. The side-effect of this is that full context
        fixtures will be set up and torn down around each test named.
        """
        # Fast path for when we don't care
        if not names or len(names) == 1:
            return 
        loader = self.loader
        plugins = self.conf.plugins
        def lazy():
            for name in names:
                plugins.beforeContext()
                yield loader.loadTestsFromName(name, module=module)
                plugins.afterContext()
        return (loader.suiteClass(lazy), [])

    def prepareTestLoader(self, loader):
        """Get handle on test loader so we can use it in loadTestsFromNames.
        """
        self.loader = loader

