Setuptools integration
======================

nose may be used with the setuptools_ test command. Simply specify
nose.collector as the test suite in your setup file::

  setup (
      # ...
      test_suite = 'nose.collector'
  )

Then to find and run tests, you can run::

  python setup.py test

When running under setuptools, you can configure nose settings via the
environment variables detailed in the nosetests script usage message,
or the setup.cfg or ~/.noserc or ~/.nose.cfg config files.

Please note that when run under the setuptools test command, some plugins will
not be available, including the builtin coverage, and profiler plugins.
 
nose also includes its own setuptools command, ``nosetests``, that
provides support for all plugins and command line options. See
nose.commands_ for more information about the ``nosetests`` command.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _nose.commands: #commands

