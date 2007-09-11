Excluding Unwanted Packages
---------------------------

Normally, nose discovery descends into all packages. Plugins can
change this behavior by implementing ``wantDirectory()``.

In this example, we have a wanted package called ``wanted_package``
and an unwanted package called ``unwanted_package``. 

    >>> import os
    >>> import sys
    >>> support = os.path.join(os.path.dirname(__file__), 'support')
    >>> os.listdir(support)
    ['unwanted_package', 'wanted_package']

When we run nose normally, tests are loaded from both packages. The
only config change we're making here is to send the test output to
sys.stdout, so doctest will catch it.

    >>> import nose
    >>> from nose.config import Config
    >>> from nose.plugins import Plugin, PluginManager
    >>> config = Config(stream=sys.stdout,
    ...                 plugins=PluginManager())
    >>> argv = [__file__, '-v', support]
    >>> nose.run(argv=argv,
    ...          config=config) # doctest: +REPORT_NDIFF +ELLIPSIS
    unwanted_package.test_spam.test_spam ... ok
    wanted_package.test_eggs.test_eggs ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...
    <BLANKLINE>
    OK
    True

To exclude the tests in the unwanted package, we can write a simple
plugin that implements ``wantDirectory()`` and returns ``False`` if
the basename of the directory is ``"unwanted_package"``. This will
prevent nose from descending into the unwanted package.

    >>> class UnwantedPackagePlugin(Plugin):
    ...     # no command line arg needed to activate plugin
    ...     enabled = True
    ...     name = "unwanted-package"
    ...     
    ...     def wantDirectory(self, dirname):
    ...         want = None
    ...         if os.path.basename(dirname) == "unwanted_package":
    ...             want = False
    ...         return want

To test the plugin, we'll configure a test run to use it by giving
the config instance a `PluginManager` that includes the new plugin.

    >>> config.plugins = PluginManager(plugins=[UnwantedPackagePlugin()])

We can now execute the test run and see in the output that the test in
the unwanted package is not discovered.

    >>> nose.run(argv=argv,
    ...          config=config) # doctest: +REPORT_NDIFF +ELLIPSIS
    wanted_package.test_eggs.test_eggs ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...
    <BLANKLINE>
    OK
    True

