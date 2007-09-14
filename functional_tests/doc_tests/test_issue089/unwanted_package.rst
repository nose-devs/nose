Excluding Unwanted Packages
---------------------------

Normally, nose discovery descends into all packages. Plugins can
change this behavior by implementing `wantDirectory()`_.
    
    >>> import os
    >>> import sys
    >>> from nose.plugins import Plugin

In this example, we have a wanted package called ``wanted_package``
and an unwanted package called ``unwanted_package``. 

    >>> support = os.path.join(os.path.dirname(__file__), 'support')
    >>> support_files = [d for d in os.listdir(support)
    ...                  if not d.startswith('.')]
    >>> support_files.sort()
    >>> support_files
    ['unwanted_package', 'wanted_package']

When we run nose normally, tests are loaded from both packages. (To
avoid side-effects, the test run is configured to use no plugins and a
clean environment.)

.. Note ::

   The run() function in nose.plugins.doctests reformats test result
   output to remove timings, which will vary from run to run, and
   redirects the output to stdout.

    >>> from nose.plugins.doctests import run

..
    >>> argv = [__file__, '-v', support]
    >>> run(argv=argv) # doctest: +REPORT_NDIFF
    unwanted_package.test_spam.test_spam ... ok
    wanted_package.test_eggs.test_eggs ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...s
    <BLANKLINE>
    OK

To exclude the tests in the unwanted package, we can write a simple
plugin that implements `wantDirectory()`_ and returns ``False`` if
the basename of the directory is ``"unwanted_package"``. This will
prevent nose from descending into the unwanted package.

    >>> class UnwantedPackagePlugin(Plugin):
    ...     # no command line arg needed to activate plugin
    ...     enabled = True
    ...     name = "unwanted-package"
    ...     
    ...     def configure(self, options, conf):
    ...         pass # always on
    ...     
    ...     def wantDirectory(self, dirname):
    ...         want = None
    ...         if os.path.basename(dirname) == "unwanted_package":
    ...             want = False
    ...         return want

To test the plugin, we'll configure a test run to use it by giving
the config instance a `PluginManager` that includes the new plugin.
In this test run, the unwanted package is not discovered.

    >>> run(argv=argv,
    ...     plugins=[UnwantedPackagePlugin()]) # doctest: +REPORT_NDIFF    
    wanted_package.test_eggs.test_eggs ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    OK

.. _`wantDirectory()` : plugin_interface.html#wantDirectory
