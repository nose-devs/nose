What's new
==========

0.11 is a major release of nose, featuring several new or improved plugins,
completely revised documentation, some small, mostly backwards-compatible
changes in behavior, and numerous bug fixes.

New plugins
-----------

* :doc:`Multiprocess <plugins/multiprocess>`

  The multiprocess plugin enables splitting test runs across multiple
  processes. For some test suites, this can shorten run time tremendously.
  See also: :doc:`doc_tests/test_multiprocess/multiprocess`  

* :doc:`Log capture <plugins/logcapture>`

  The log capture plugin does for logging what the
  :doc:`capture <plugins/capture>` plugin does for stdout. All :mod:`logging`
  messages produced during a failing test are appended to the error
  output printed at the end of the test run.

* :doc:`Xunit <plugins/xunit>`
 
  The Xunit plugin produces a test result file in ant/junit xml format,
  suitable for use with `hudson`_ and other continuous integration systems
  that consume this format.

* :doc:`Collect only <plugins/collect>`
  
  The collect only plugin just collects all of your tests, it doesn't run
  them. Fixtures are also skipped, so collection should be quick.

* :doc:`Collect tests from all modules <plugins/allmodules>`

  This plugin enables collecting tests from all python modules, not just those
  that match testMatch.
  
.. _`hudson` : https://hudson.dev.java.net/

Plugin improvements
-------------------

* Doctest fixtures

  The :doc:`doctest plugin <plugins/doctests>` now supports using fixtures with
  doctest files. You can specify a module prefix (eg, "_fixture") and if a
  module exists with that prefix appended to the name of the doctest file (eg,
  "test_pillow_fixture.py" for the doctest file "test_pillow.txt"), then
  fixtures for the doctest will be extracted from the module. See
  :doc:`doc_tests/test_doctest_fixtures/doctest_fixtures` for more.

* Looping over failed tests

* HTML coverage reports

Changes
-------

* New docs

* Namespace packages

* To make it easier to use custom plugins without needing setuptools,
  :func:`nose.core.main` and :func:`nose.core.run` now support an
  :doc:`addplugins <doc_tests/test_addplugins/test_addplugins>` keyword
  argument that takes a list of additional plugins to make available. **Note**
  that adding a plugin to this list **does not** activate or enable the
  plugin, only makes it available to be enabled via command-line or
  config file settings.

* Limited IronPython support

Detailed changes
----------------

.. include :: ../CHANGELOG