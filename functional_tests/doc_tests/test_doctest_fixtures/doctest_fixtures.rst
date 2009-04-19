Doctest Fixtures
----------------

FIXME blah blah FIXME

.. include :: doctest_fixtures_fixtures.py
   :literal:

FIXME examples
   
    >>> something
    'Something?'
    
    >>> 1
    1
    >>> count
    1

This whole file is one doctest test. setup_test doesn't do what you think!
It exists to give you access to the test case and examples, but it runs
*once*, before all of them, not before each.

    >>> count
    1

   
Fixtures for a doctest file may define any or all of the following methods:

setup/setup_module/setupModule/setUpModule (module)
===================================================

Example::

  def setup_module(module):
      module.called[:] = []

teardown/teardown_module/teardownModule/tearDownModule (module)
===============================================================

Example::

  def teardown_module(module):
      module.called[:] = []
      module.done = True

setup_test(test)
================

Called before each test. Argument is the *doctest.DocTest* object, *not* a
unittest.TestCase.

Example::

  def setup_test(test):
      called.append(test)
      test.globs['count'] = len(called)
  setup_test.__test__ = False
      

This is another example.


And this is yet another example.


teardown_test(test)
===================

Called after each test, unless setup raised an uncaught exception. Argument is
the *doctest.DocTest* object, *not* a unittest.TestCase.

Example::

  def teardown_test(test):
      pass
  teardown_test.__test__ = False
  
Bottom line: setup_test, teardown_test have access to the *doctest test*,
while setup, setup_module, etc have access to the *fixture* module.

globs(globs)
============




