Plugin Interface
================

Plugin base class
-----------------

.. autoclass :: nose.plugins.base.Plugin
   :members:

Nose plugin API
---------------

While it is recommended that plugins subclass nose.plugins.Plugin, the only
requirements for a plugin are that it implement the methods `options(self,
parser, env)` and `configure(self, options, conf)`, and have the attributes
`enabled`, `name` and `score`.

Plugins may implement any or all of the methods documented below. Please note
that they *must not* subclass `IPluginInterface`; `IPluginInterface` is a only
description of the plugin API.

When plugins are called, the first plugin that implements a method and returns
a non-None value wins, and plugin processing ends. The exceptions to this are
methods marked as `generative` or `chainable`.  `generative` methods combine
the output of all plugins that respond with an iterable into a single
flattened iterable response (a generator, really). `chainable` methods pass
the results of calling plugin A as the input to plugin B, where the positions
in the chain are determined by the plugin sort order, which is in order by
`score` descending.

In general, plugin methods correspond directly to methods of
`nose.selector.Selector`, `nose.loader.TestLoader` and
`nose.result.TextTestResult` are called by those methods when they are
called. In some cases, the plugin hook doesn't neatly match the method in
which it is called; for those, the documentation for the hook will tell you
where in the test process it is called.

Plugin hooks fall into four broad categories: selecting and loading tests,
handling errors raised by tests, preparing objects used in the testing
process, and watching and reporting on test results.

Selecting and loading tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To alter test selection behavior, implement any necessary `want*` methods as
outlined below. Keep in mind, though, that when your plugin returns True from
a `want*` method, you will send the requested object through the normal test
collection process. If the object represents something from which normal tests
can't be collected, you must also implement a loader method to load the tests.

Examples:

* The builtin doctests plugin implements `wantFile` to enable
  loading of doctests from files that are not python modules. It
  also implements `loadTestsFromModule` to load doctests from
  python modules, and `loadTestsFromFile` to load tests from the
  non-module files selected by `wantFile`.
   
* The builtin attrib plugin implements `wantFunction` and
  `wantMethod` so that it can reject tests that don't match the
  specified attributes.

Handling errors
^^^^^^^^^^^^^^^

To alter error handling behavior -- for instance to catch a certain class of 
exception and handle it differently from the normal error or failure handling
-- you should subclass :class:`nose.plugins.errorclass.ErrorClassPlugin`. See `the section on ErrorClass plugins`_ for more details.

Examples:

* The builtin skip and deprecated plugins are ErrorClass plugins.

.. _the section on ErrorClass plugins: errorclasses.html

Preparing test objects
^^^^^^^^^^^^^^^^^^^^^^

To alter, get a handle on, or replace test framework objects such
as the loader, result, runner, and test cases, use the appropriate
prepare methods. The simplest reason to use prepare is if you need
to use an object yourself. For example, the isolate plugin
implements `prepareTestLoader` so that it can use the test loader
later on to load tests. If you return a value from a prepare
method, that value will be used in place of the loader, result,
runner or test case, respectively. When replacing test cases, be
aware that you are replacing the entire test case -- including the
whole `run(result)` method of the `unittest.TestCase` -- so if you
want normal unittest test result reporting, you must implement the
same calls to result as `unittest.TestCase.run`.

Examples:

* The builtin isolate plugin implements `prepareTestLoader` but
  does not replace the test loader.

* The builtin profile plugin implements `prepareTest` and does
  replace the top-level test case by returning the case wrapped in
  the profiler function.

Watching or reporting on tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To record information about tests or other modules imported during
the testing process, output additional reports, or entirely change
test report output, implement any of the methods outlined below that
correspond to TextTestResult methods.

Examples:

* The builtin cover plugin implements `begin` and `report` to
  capture and report code coverage metrics for all or selected modules
  loaded during testing.
   
* The builtin profile plugin implements `begin`, `prepareTest` and
  `report` to record and output profiling information. In this
  case, the plugin's `prepareTest` method constructs a function that
  runs the test through the hotshot profiler's runcall() method.

Plugin interface methods
------------------------

.. autoclass :: nose.plugins.base.IPluginInterface
   :members: