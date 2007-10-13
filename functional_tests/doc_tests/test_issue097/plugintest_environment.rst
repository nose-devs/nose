nose.plugins.plugintest and os.environ
--------------------------------------

`nose.plugins.plugintest.PluginTester`_ and
`nose.plugins.plugintest.run()`_ are utilities for testing nose
plugins.  When testing plugins, it should be possible to control the
environment seen plugins under test, and that environment should never
be affected by ``os.environ``.

    >>> import os
    >>> import unittest
    >>> from nose.config import Config
    >>> from nose.plugins import Plugin
    >>> from nose.plugins.builtin import FailureDetail, Capture
    >>> from nose.plugins.plugintest import PluginTester

Our test plugin takes no command-line arguments and simply prints the
environment it's given by nose.

    >>> class PrintEnvPlugin(Plugin):
    ...     name = "print-env"
    ...
    ...     # no command line arg needed to activate plugin
    ...     enabled = True
    ...     def configure(self, options, conf):
    ...         if not self.can_configure:
    ...             return
    ...         self.conf = conf
    ...
    ...     def options(self, parser, env={}):
    ...         print env

The class under test, PluginTester, is designed to be used by
subclassing.

    >>> class Tester(PluginTester):
    ...    activate = "-v"
    ...    plugins = [PrintEnvPlugin(),
    ...               FailureDetail(),
    ...               Capture(),
    ...               ]
    ...
    ...    def makeSuite(self):
    ...        return unittest.TestSuite(tests=[])


For the purposes of this test, we need a known ``os.environ``.

    >>> old_environ = os.environ
    >>> os.environ = {"spam": "eggs"}

If ``env`` is not overridden, the default is an empty ``env``.

    >>> tester = Tester()
    >>> tester.setUp()
    {}

An empty ``env`` is respected...

    >>> class EmptyEnvTester(Tester):
    ...    env = {}

    >>> tester = EmptyEnvTester()
    >>> tester.setUp()
    {}

... as is a non-empty ``env``.

    >>> class NonEmptyEnvTester(Tester):
    ...    env = {"foo": "bar"}

    >>> tester = NonEmptyEnvTester()
    >>> tester.setUp()
    {'foo': 'bar'}


``nose.plugins.plugintest.run()`` should work analogously.

    >>> from nose.plugins.plugintest import run

    >>> run(suite=unittest.TestSuite(tests=[]),
    ...     plugins=[PrintEnvPlugin()]) # doctest: +REPORT_NDIFF
    {}
    ----------------------------------------------------------------------
    Ran 0 tests in ...s
    <BLANKLINE>
    OK

    >>> run(env={},
    ...     suite=unittest.TestSuite(tests=[]),
    ...     plugins=[PrintEnvPlugin()]) # doctest: +REPORT_NDIFF
    {}
    ----------------------------------------------------------------------
    Ran 0 tests in ...s
    <BLANKLINE>
    OK

    >>> run(env={"foo": "bar"},
    ...     suite=unittest.TestSuite(tests=[]),
    ...     plugins=[PrintEnvPlugin()]) # doctest: +REPORT_NDIFF
    {'foo': 'bar'}
    ----------------------------------------------------------------------
    Ran 0 tests in ...s
    <BLANKLINE>
    OK


Clean up.

    >>> os.environ = old_environ
