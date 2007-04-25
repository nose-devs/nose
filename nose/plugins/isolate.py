"""Use the isolation plugin with --with-isolation or the
NOSE_WITH_ISOLATION environment variable to clean sys.modules before
and after each test module is executed.

The isolation module is in effect the same as including the following
functions in every test module and test package __init__.py:

    >>> def setup(module):
    ...     module._mods = sys.modules.copy()
    
    >>> def teardown(module):
    ...     to_del = [ m for m in sys.modules.keys() if m not in
    ...                module._mods ]
    ...     for mod in to_del:
    ...         del sys.modules[mod]
    ...     sys.modules.update(module._mods)

PLEASE NOTE that this plugin MAY NOT be used in combination with the
coverage plugin, as coverage data and state will be flushed after each
test module is run.

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
        to_del = [ m for m in sys.modules.keys() if
                       m not in mods ]
        if to_del:
            log.debug('removing sys modules entries: %s', to_del)
            for mod in to_del:
                del sys.modules[mod]
        sys.modules.update(mods)
    
#     def startTest(self, test):
#         """Save the state of sys.modules if we're starting a test module
#         """
#         if isinstance(test, TestModule):
#             log.debug('isolating sys.modules changes in %s', test)
#             self._mods = sys.modules.copy()
            
#     def stopTest(self, test):
#         """Restore the saved state of sys.modules if we're ending a test module
#         """
#         if isinstance(test, TestModule):            
#             to_del = [ m for m in sys.modules.keys() if
#                        m not in self._mods ]
#             if to_del:
#                 log.debug('removing sys modules entries: %s', to_del)
#                 for mod in to_del:
#                     del sys.modules[mod]
#             sys.modules.update(self._mods)

