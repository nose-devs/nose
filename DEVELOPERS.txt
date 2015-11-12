Hello and welcome!  Thanks for taking the time to work on Nose.

Run the Test Suite
==================

Install `tox`_ so that it's accessible on $PATH somehow.  Then cd into the source and type::

  $ tox

.. _`tox`: http://codespeak.net/tox/

That will try to run tests in all of the Python interpreters that Nose
supports.  If you don't have one of those versions installed please ask for
assistance so you don't develop an incompatible feature.

For a quick spot check of the tests you can test against a specific version
like this::

  $ tox -e py26
  
Only run a portion of tests
===========================

To only run the xunit tests in one environment for example:

  $ ./run_tests.sh -e py26 -- unit_tests/test_xunit.py

TDD
===

For a fast feedback cycle on a specific area of nose, you can use [sniffer](https://pypi.python.org/pypi/sniffer).
The following example watches your checkout and runs the xunit tests continuously:

  $ sniffer -x unit_tests/test_xunit.py

All Features Must Have Tests
============================

Well, duh.  If you get stuck on this just ask.  There are lots of ways to
make quick regression tests out of nose based suites.

Code Style
==========

Please follow `PEP8`_ for all contributed code.  Specifically, please keep
the window width to 80 chars and follow the PEP8 formatting style.

.. _`PEP8`: http://www.python.org/dev/peps/pep-0008/
