"""Writing Plugins
---------------

nose supports setuptools_ entry point plugins for test collection,
selection, observation and reporting. There are two basic rules for plugins:

 * Plugin classes should subclass `nose.plugins.Plugin`_.
 * Plugins may implement any of the methods described in the class
   PluginInterface in nose.plugins.base. Please note that this class is for
   documentary purposes only; plugins may not subclass PluginInterface.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _nose.plugins.Plugin: http://python-nose.googlecode.com/svn/trunk/nose/plugins/base.py
   
Registering
===========

For nose to find a plugin, it must be part of a package that uses
setuptools, and the plugin must be included in the entry points defined
in the setup.py for the package::

  setup(name='Some plugin',
        ...
        entry_points = {
            'nose.plugins': [
                'someplugin = someplugin:SomePlugin'
                ]
            },
        ...
        )

Once the package is installed with install or develop, nose will be able
to load the plugin.

Defining options
================

All plugins must implement the methods ``add_options(self, parser, env)``
and ``configure(self, options, conf)``. Subclasses of nose.plugins.Plugin
that want the standard options should call the superclass methods.

nose uses optparse.OptionParser from the standard library to parse
arguments. A plugin's ``add_options()`` method receives a parser
instance. It's good form for a plugin to use that instance only to add
additional arguments that take only long arguments (--like-this). Most
of nose's built-in arguments get their default value from an environment
variable. This is a good practice because it allows options to be
utilized when run through some other means than the nosetests script.

A plugin's ``configure()`` method receives the parsed ``OptionParser`` options 
object, as well as the current config object. Plugins should configure their
behavior based on the user-selected settings, and may raise exceptions
if the configured behavior is nonsensical.

Logging
=======

nose uses the logging classes from the standard library. To enable users
to view debug messages easily, plugins should use ``logging.getLogger()`` to
acquire a logger in the ``nose.plugins`` namespace.

Recipes
=======

 * Writing a plugin that monitors or controls test result output

   Implement any or all of ``addError``, ``addFailure``, etc., to monitor test
   results. If you also want to monitor output, implement
   ``setOutputStream`` and keep a reference to the output stream. If you
   want to prevent the builtin ``TextTestResult`` output, implement
   ``setOutputSteam`` and *return a dummy stream*. The default output will go
   to the dummy stream, while you send your desired output to the real stream.
 
   Example: `examples/html_plugin/htmlplug.py`_

 * Writing a plugin that loads tests from files other than python modules

   Implement ``wantFile`` and ``loadTestsFromPath``. In ``wantFile``, return
   True for files that you want to examine for tests. In ``loadTestsFromPath``,
   for those files, return a TestSuite or other iterable containing
   TestCases. ``loadTestsFromPath`` may also be a generator.
 
   Example: `nose.plugins.doctests`_

 * Writing a plugin that prints a report

   Implement begin if you need to perform setup before testing
   begins. Implement ``report`` and output your report to the provided stream.
 
   Examples: `nose.plugins.cover`_, `nose.plugins.profile`_, `nose.plugins.missed`_

 * Writing a plugin that selects or rejects tests

   Implement any or all ``want*``  methods. Return False to reject the test
   candidate, True to accept it -- which  means that the test candidate
   will pass through the rest of the system, so you must be prepared to
   load tests from it if tests can't be loaded by the core loader or
   another plugin -- and None if you don't care.

   Examples: `nose.plugins.attrib`_, `nose.plugins.doctests`_

Examples
========

See `nose.plugins.attrib`_, `nose.plugins.cover`_, `nose.plugins.doctests`_
and `nose.plugins.profile`_ for examples. Further examples may be found the
examples_ directory in the nose source distribution.

.. _examples/html_plugin/htmlplug.py: http://python-nose.googlecode.com/svn/trunk/examples/html_plugin/htmlplug.py
.. _examples: http://python-nose.googlecode.com/svn/trunk/examples
.. _nose.plugins.attrib: http://python-nose.googlecode.com/svn/trunk/nose/plugins/attrib.py
.. _nose.plugins.cover: http://python-nose.googlecode.com/svn/trunk/nose/plugins/cover.py
.. _nose.plugins.doctests: http://python-nose.googlecode.com/svn/trunk/nose/plugins/doctests.py
.. _nose.plugins.missed: http://python-nose.googlecode.com/svn/trunk/nose/plugins/missed.py
.. _nose.plugins.profile: http://python-nose.googlecode.com/svn/trunk/nose/plugins/profile.py

"""
from __future__ import generators

import logging
import pkg_resources
from inspect import isclass
from warnings import warn
from nose.plugins.base import *

builtin_plugins = ('attrib', 'cover', 'doctests', 'isolate', 'missed', 'prof')
log = logging.getLogger(__name__)

def call_plugins(plugins, method, *arg, **kw):
    """Call all method on plugins in list, that define it, with provided
    arguments. The first response that is not None is returned.
    """
    for plug in plugins:
        func = getattr(plug, method, None)
        if func is None:
            continue
        log.debug("call plugin %s: %s", plug.name, method)
        result = func(*arg, **kw)
        if result is not None:
            return result
    return None
        
def load_plugins(builtin=True, others=True):
    """Load plugins, either builtin, others, or both.
    """
    loaded = []
    if builtin:
        for name in builtin_plugins:
            try:
                parent = __import__(__name__, globals(), locals(), [name])
                pmod = getattr(parent, name)
                for entry in dir(pmod):
                    obj = getattr(pmod, entry)
                    if (isclass(obj)
                        and issubclass(obj, Plugin)
                        and obj is not Plugin
                        and not obj in loaded):
                        log.debug("load builtin plugin %s (%s)" % (name, obj))
                        yield obj
                        loaded.append(obj)
            except KeyboardInterrupt:
                raise
            except Exception, e:
                warn("Unable to load builtin plugin %s: %s" % (name, e),
                     RuntimeWarning)
    if not others:
        return
    for ep in pkg_resources.iter_entry_points('nose.plugins'):
        log.debug("load plugin %s" % ep)
        try:
            plug = ep.load()
        except KeyboardInterrupt:
            raise
        except Exception, e:
            # never want a plugin load to kill the test run
            # but we can't log here because the logger is not yet
            # configured
            warn("Unable to load plugin %s: %s" % (ep, e), RuntimeWarning)
            continue
        if plug.__module__.startswith('nose.plugins'):
            # already loaded as a builtin
            pass
        elif plug not in loaded:
            yield plug
            loaded.append(plug)


