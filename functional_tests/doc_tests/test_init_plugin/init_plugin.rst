Runing Initialization Code Before the Test Run
----------------------------------------------

Many applications, especially those using web frameworks like Pylons_
or Django_, can't be tested without first being configured or
otherwise initialized. Plugins can fulfill this requirement by
implementing `begin()`_.

    >>> import os
    >>> from nose.config import Config
    >>> from nose.plugins import Plugin, PluginManager

In this example, we'll use a very simple example: a widget class that
can't be tested without a configuration.

Here's the widget class. It's configured at the class or instance
level by setting the ``cfg`` attribute to a dictionary.

    >>> class ConfigurableWidget(object):
    ...     cfg = None
    ...     def can_frobnicate(self):
    ...         return self.cfg.get('can_frobnicate', True)
    ...     def likes_cheese(self):
    ...         return self.cfg.get('likes_cheese', True)

Gere are the tests. The tests only test that the widget's methods
can be called without raising any exceptions.

    >>> import unittest
    >>> class TestConfigurableWidget(unittest.TestCase):
    ...     def setUp(self):
    ...         self.widget = ConfigurableWidget()
    ...     def test_can_frobnicate(self):
    ...         """Widgets can frobnicate (or not)"""
    ...         self.widget.can_frobnicate()
    ...     def test_likes_cheese(self):
    ...         """Widgets might like cheese"""
    ...         self.widget.likes_cheese()

The tests are bundled into a suite that we can pass to the test runner.

    >>> suite = unittest.TestSuite([
    ...     TestConfigurableWidget('test_can_frobnicate'),
    ...     TestConfigurableWidget('test_likes_cheese')])

When we run tests without first configuring the ConfigurableWidget,
the tests fail.

    >>> from nose.plugins.doctests import run

    >>> config = Config(plugins=PluginManager())
    >>> argv = [__file__, '-v']
    >>> env = {}
    >>> run(argv=argv, env=env, config=config,
    ...     suite=suite)  # doctest: +REPORT_NDIFF
    Widgets can frobnicate (or not) ... ERROR
    Widgets might like cheese ... ERROR
    <BLANKLINE>
    ======================================================================
    ERROR: Widgets can frobnicate (or not)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "<doctest init_plugin.rst[5]>", line 6, in test_can_frobnicate
        self.widget.can_frobnicate()
      File "<doctest init_plugin.rst[3]>", line 4, in can_frobnicate
        return self.cfg.get('can_frobnicate', True)
    AttributeError: 'NoneType' object has no attribute 'get'
    <BLANKLINE>
    ======================================================================
    ERROR: Widgets might like cheese
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "<doctest init_plugin.rst[5]>", line 9, in test_likes_cheese
        self.widget.likes_cheese()
      File "<doctest init_plugin.rst[3]>", line 6, in likes_cheese
        return self.cfg.get('likes_cheese', True)
    AttributeError: 'NoneType' object has no attribute 'get'
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...s
    <BLANKLINE>
    FAILED (errors=2)

To configure the widget system before running tests, write a plugin
that implements `begin()`_ and initializes the system with a
hard-coded configuration. Later, we'll extend the plugin to
accept a command-line argument specifying the configuration file.

    >>> class ConfiguringPlugin(Plugin):
    ...     enabled = True
    ...     def begin(self):
    ...         ConfigurableWidget.cfg = {}

Now configure and execute a new test run using the plugin, which will
inject the hard-coded configuration.

    >>> config.plugins = PluginManager(plugins=[ConfiguringPlugin()])
    >>> run(argv=argv, env=env, config=config,
    ...     suite=suite)  # doctest: +REPORT_NDIFF
    Widgets can frobnicate (or not) ... ok
    Widgets might like cheese ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...s
    <BLANKLINE>
    OK

This time the tests pass, because the widget class is configured.

.. Note :: TODO

   Add another, better plugin that loads a config file based
   specified on command line.
