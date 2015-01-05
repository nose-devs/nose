Testing tools
-------------

The nose.tools module provides a number of testing aids that you may
find useful, including decorators for restricting test execution time
and testing for exceptions, and all of the same assertX methods found
in `unittest.TestCase` (only spelled in :pep:`8#function-names`
fashion, so `assert_equal` rather than `assertEqual`).

Under Python older than 2.7 unittest2_ will be used instead to provide
backported unittest_ 2.7+ assert macros.

.. _unittest2: https://pypi.python.org/pypi/unittest2
.. _unittest: http://docs.python.org/2/library/unittest.html

.. automodule :: nose.tools
   :members:
