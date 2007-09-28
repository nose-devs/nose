"""
Writing Plugins
---------------

nose supports plugins for test collection, selection, observation and
reporting. There are two basic rules for plugins:

* Plugin classes should subclass `nose.plugins.Plugin`_.
* Plugins may implement any of the methods described in the class
  PluginInterface in nose.plugins.base. Please note that this class is for
  documentary purposes only; plugins may not subclass PluginInterface.

.. _nose.plugins.Plugin: http://python-nose.googlecode.com/svn/trunk/nose/plugins/base.py
   
Registering
===========

.. Note:: Important note: the following applies only to the default \
plugin manager. Other plugin managers may use different means to \
locate and load plugins.

For nose to find a plugin, it must be part of a package that uses
setuptools_, and the plugin must be included in the entry points defined
in the setup.py for the package::

  setup(name='Some plugin',
        ...
        entry_points = {
            'nose.plugins.0.10': [
                'someplugin = someplugin:SomePlugin'
                ]
            },
        ...
        )

Once the package is installed with install or develop, nose will be able
to load the plugin.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

Defining options
================

All plugins must implement the methods ``options(self, parser, env)``
and ``configure(self, options, conf)``. Subclasses of nose.plugins.Plugin
that want the standard options should call the superclass methods.

nose uses optparse.OptionParser from the standard library to parse
arguments. A plugin's ``options()`` method receives a parser
instance. It's good form for a plugin to use that instance only to add
additional arguments that take only long arguments (--like-this). Most
of nose's built-in arguments get their default value from an environment
variable.

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

* Writing a plugin that handles exceptions

  Subclass `ErrorClassPlugin`_.

  Examples: `nose.plugins.deprecated`_, `nose.plugins.skip`_

* Writing a plugin that adds detail to error reports

  Implement ``formatError`` and/or ``formatFailture``. The error tuple
  you return (error class, error message, traceback) will replace the
  original error tuple.

  Examples: `nose.plugins.capture`_, `nose.plugins.failuredetail`_

* Writing a plugin that loads tests from files other than python modules

  Implement ``wantFile`` and ``loadTestsFromFile``. In ``wantFile``,
  return True for files that you want to examine for tests. In
  ``loadTestsFromFile``, for those files, return an iterable
  containing TestCases (or yield them as you find them;
  ``loadTestsFromFile`` may also be a generator).
 
  Example: `nose.plugins.doctests`_

* Writing a plugin that prints a report

  Implement begin if you need to perform setup before testing
  begins. Implement ``report`` and output your report to the provided stream.
 
  Examples: `nose.plugins.cover`_, `nose.plugins.prof`_

* Writing a plugin that selects or rejects tests

  Implement any or all ``want*``  methods. Return False to reject the test
  candidate, True to accept it -- which  means that the test candidate
  will pass through the rest of the system, so you must be prepared to
  load tests from it if tests can't be loaded by the core loader or
  another plugin -- and None if you don't care.
 
  Examples: `nose.plugins.attrib`_, `nose.plugins.doctests`_,
  `nose.plugins.testid`_

More Examples
=============

See any builtin plugin or example plugin in the examples_ directory in
the nose source distribution.

.. _examples/html_plugin/htmlplug.py: http://python-nose.googlecode.com/svn/trunk/examples/html_plugin/htmlplug.py
.. _examples: http://python-nose.googlecode.com/svn/trunk/examples


Testing Plugins
===============

The plugin interface is well-tested enough so that you can safely unit
test your use of its hooks with some level of confidence. However,
there is a mixin for unittest.TestCase called PluginTester that's
designed to test plugins in their native runtime environment.

Here's a simple example with a do-nothing plugin and a composed suite.

    >>> import unittest
    >>> from nose.plugins import Plugin, PluginTester
    >>> class FooPlugin(Plugin):
    ...     pass
    >>> class TestPluginFoo(PluginTester, unittest.TestCase):
    ...     activate = '--with-foo'
    ...     plugins = [FooPlugin()]
    ...     def test_foo(self):
    ...         for line in self.output:
    ...             # i.e. check for patterns
    ...             pass
    ... 
    ...         # or check for a line containing ...
    ...         assert "ValueError" in self.output
    ...     def makeSuite(self):
    ...         class TC(unittest.TestCase):
    ...             def runTest(self):
    ...                 raise ValueError("I hate foo")
    ...         return unittest.TestSuite([TC()])
    ...
    >>> res = unittest.TestResult()
    >>> case = TestPluginFoo('test_foo')
    >>> case(res)
    >>> res.errors
    []
    >>> res.failures
    []
    >>> res.wasSuccessful()
    True
    >>> res.testsRun
    1

Here is a more complex example of testing a plugin that has extra arguments and 
reads environment variables ::
    
    >>> import unittest, os
    >>> from nose.plugins import Plugin, PluginTester
    >>> class FancyOutputter(Plugin):
    ...     name = "fancy"
    ...     def configure(self, options, conf):
    ...         Plugin.configure(self, options, conf)
    ...         if not self.enabled:
    ...             return
    ...         self.fanciness = 1
    ...         if options.more_fancy:
    ...             self.fanciness = 2
    ...         if 'EVEN_FANCIER' in self.env:
    ...             self.fanciness = 3
    ... 
    ...     def options(self, parser, env=os.environ):
    ...         self.env = env
    ...         parser.add_option('--more-fancy', action='store_true')
    ...         Plugin.options(self, parser, env=env)
    ... 
    ...     def report(self, stream):
    ...         stream.write("FANCY " * self.fanciness)
    ... 
    >>> class TestFancyOutputter(PluginTester, unittest.TestCase):
    ...     activate = '--with-fancy' # enables the plugin
    ...     plugins = [FancyOutputter()]
    ...     args = ['--more-fancy']
    ...     env = {'EVEN_FANCIER': '1'}
    ... 
    ...     def test_fancy_output(self):
    ...         assert "FANCY FANCY FANCY" in self.output, (
    ...                                         "got: %s" % self.output)
    ...     def makeSuite(self):
    ...         class TC(unittest.TestCase):
    ...             def runTest(self):
    ...                 raise ValueError("I hate fancy stuff")
    ...         return unittest.TestSuite([TC()])
    ... 
    >>> res = unittest.TestResult()
    >>> case = TestFancyOutputter('test_fancy_output')
    >>> case(res)
    >>> res.errors
    []
    >>> res.failures
    []
    >>> res.wasSuccessful()
    True
    >>> res.testsRun
    1
    
"""
from nose.plugins.base import Plugin
from nose.plugins.manager import *
from nose.plugins.plugintest import PluginTester

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    