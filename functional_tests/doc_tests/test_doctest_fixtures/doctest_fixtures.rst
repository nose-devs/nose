Doctest Fixtures
----------------

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
      
    >>> 1
    1

This is another example.

    >>> count
    1

And this is yet another example.

    >>> count
    1

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

    >>> something
    'Something?'



