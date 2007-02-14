0.10 dev branch -- unstable
---------------------------

WARNING
=======

This branch is highly unstable and under active development. Unless
you are working on nose itself, you should not be using this branch!

What's going on here?
=====================

0.10 will be a major release of nose, with deep changes to test
loading and running that aim to make nose's parts (the TestLoader,
etc) more plug-in compatible with unittest, as well as simpler to
understand and hack. Other goals include:

* Making use of commandline arguments more intuitive. Currently you
  *can't* say `nosetests foo.py` to make nose load tests from foo.py
  -- nose doesn't think its a test file. You know better, but nose
  won't listen. This is dumb.

* Making sure fixtures (setup/teardown) are only ever executed when
  there are tests underneath them.

* Providing more hooks for plugins to control loading of tests,
  imports, and fixture state.

* Providing a single interface around all test types, to help plugins
  interact with tests more easily.

This involves some major changes to how nose loads and runs tests.

Changes to loading
==================

Currently, nose's TestLoader has many methods with the same names as
unittests's TestLoader, but those methods take different arguments and
in general can't be plugged in where unittest's methods work now. The
major reason for this was the design decision that nose should be
discovery-first, that is, it should never operate on a test it didn't
discover.

Changes to fixtures
===================

Currently, module and package level fixtures are executed by test
suite subclasses, in those suite's setUp and tearDown methods. This
produces a number of undesireable side effects, including that
fixtures execute even when no tests are collected, and that it's
impossible to simple walk the discovery tree and collect all tests
before (or instead of) running them.

nose 0.10 will fix this by separating the fixture context from the
loader, using a new class (nose.fixture.Context) to manage the
fixtures that surround any group of tests. One fixture context will be
used per loader instance, and each test will be wrapped in a
contexualized test case instance that references the context. The
context tracks which tests belong to what modules, and it runs the
module-level setUp before the first test from any module and the
module-level tearDown after the last test from any module (if the
module-level setUp succeeded). This works only because loading and
discovery are now depth-first within modules, so all tests from a
module (including packages and subpackages) are loaded before the
first is executed.

More details to come (watch this space)
