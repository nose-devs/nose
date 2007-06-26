"""Implements nose test program and collector.
"""
from __future__ import generators

import logging
import os
import re
import sys
import time
import unittest
from warnings import warn

from nose.config import Config, all_config_files
from nose.loader import defaultTestLoader
from nose.plugins.manager import DefaultPluginManager, RestrictedPluginManager
from nose.result import TextTestResult
from nose.util import isclass, tolist


log = logging.getLogger('nose.core')
compat_24 = sys.version_info >= (2, 4)

__all__ = ['TestProgram', 'main', 'run', 'run_exit', 'runmodule', 'collector',
           'TextTestRunner']

            
class TextTestRunner(unittest.TextTestRunner):
    """Test runner that uses nose's TextTestResult to enable errorClasses,
    as well as providing hooks for plugins to override or replace the test
    output stream, results, and the test case itself.
    """    
    def __init__(self, stream=sys.stderr, descriptions=1, verbosity=1,
                 config=None):
        if config is None:
            config = Config()
        self.config = config
        unittest.TextTestRunner.__init__(self, stream, descriptions, verbosity)

    
    def _makeResult(self):
        return TextTestResult(self.stream,
                              self.descriptions,
                              self.verbosity,
                              self.config)

    def run(self, test):
        """Overrides to provide plugin hooks and defer all output to
        the test result class.
        """
        wrapper = self.config.plugins.prepareTest(test)
        if wrapper is not None:
            test = wrapper
        
        # plugins can decorate or capture the output stream
        wrapped = self.config.plugins.setOutputStream(self.stream)
        if wrapped is not None:
            self.stream = wrapped
            
        result = self._makeResult()
        start = time.time()
        test(result)
        stop = time.time()
        result.printErrors()
        result.printSummary(start, stop)
        self.config.plugins.finalize(result)
        return result

    
class TestProgram(unittest.TestProgram):
    r"""usage: %prog [options] [names]
    
    nose provides extended test discovery and running features for
    unittest.
    
    nose collects tests automatically from python source files,
    directories and packages found in its working directory (which
    defaults to the current working directory). Any python source file,
    directory or package that matches the testMatch regular expression
    (by default: (?:^|[\b_\.-])[Tt]est) will be collected as a test (or
    source for collection of tests). In addition, all other packages
    found in the working directory will be examined for python source files
    or directories that match testMatch. Package discovery descends all
    the way down the tree, so package.tests and package.sub.tests and
    package.sub.sub2.tests will all be collected.
    
    Within a test directory or package, any python source file matching
    testMatch will be examined for test cases. Within a test module,
    functions and classes whose names match testMatch and TestCase
    subclasses with any name will be loaded and executed as tests. Tests
    may use the assert keyword or raise AssertionErrors to indicate test
    failure. TestCase subclasses may do the same or use the various
    TestCase methods available.
        
    Selecting Tests
    ---------------

    To specify which tests to run, pass test names on the command line:

      %prog only_test_this.py

    Test names specified may be file or module names, and may optionally
    indicate the test case to run by separating the module or file name
    from the test case name with a colon. Filenames may be relative or
    absolute. Examples:

      %prog test.module
      %prog another.test:TestCase.test_method
      %prog a.test:TestCase
      %prog /path/to/test/file.py:test_function
      
    You may also change the working directory where nose looks for tests,
    use the -w switch:

      %prog -w /path/to/tests

    Note however that support for multiple -w arguments is deprecated
    in this version and will be removed in a future release, since as
    of nose 0.10 you can get the same behavior by specifying the
    target directories *without* the -w switch:

      %prog /path/to/tests /another/path/to/tests

    Further customization of test selection and loading is possible
    through the use of plugins.

    Test result output is identical to that of unittest, except for
    the additional features (error classes, and plugin-supplied
    features such as output capture and assert introspection) detailed
    in the options below.

    Configuration
    -------------

    In addition to passing command-line options, you may also put configuration
    options in a .noserc or nose.cfg file in your home directory. These are
    standard .ini-style config files. Put your nosetests configuration in a
    [nosetests] section, with the -- prefix removed:

      [nosetests]
      verbosity=3
      with-doctest=1

    All configuration files that are found will be loaded and their options
    combined.
    """
    verbosity = 1

    def __init__(self, module=None, defaultTest='.', argv=None,
                 testRunner=None, testLoader=None, env=None, config=None,
                 suite=None, exit=True):
        if env is None:
            env = os.environ
        if config is None:
            config = self.makeConfig(env)
        self.config = config
        self.suite = suite
        self.exit = exit
        unittest.TestProgram.__init__(
            self, module=module, defaultTest=defaultTest,
            argv=argv, testRunner=testRunner, testLoader=testLoader)

    def makeConfig(self, env):
        """Load a Config, pre-filled with user config files if any are
        found.
        """
        cfg_files = all_config_files()
        return Config(
            env=env, files=cfg_files, plugins=DefaultPluginManager())
        
    def parseArgs(self, argv):
        """Parse argv and env and configure running environment.
        """
        log.debug("parseArgs is called %s", argv)

        self.config.configure(argv, doc=TestProgram.__doc__)
        log.debug("configured %s", self.config)

        # quick outs: version, plugins (optparse would have already
        # caught and exited on help)
        if self.config.options.version:
            from nose import __version__
            sys.stdout = sys.__stdout__
            print "%s version %s" % (os.path.basename(sys.argv[0]), __version__)
            sys.exit(0)

        if self.config.options.showPlugins:
            self.showPlugins()
            sys.exit(0)
        
        if self.testLoader is None:
            self.testLoader = defaultTestLoader(config=self.config)
        elif isclass(self.testLoader):
            self.testLoader = self.testLoader(config=self.config)
        plug_loader = self.config.plugins.prepareTestLoader(self.testLoader)
        if plug_loader is not None:
            self.testLoader = plug_loader
        log.debug("test loader is %s", self.testLoader)
        
        # FIXME if self.module is a string, add it to self.testNames? not sure

        if self.config.testNames:
            self.testNames = self.config.testNames
        else:
            self.testNames = (self.defaultTest,)
        log.debug('Test names are %s', self.testNames)
        if self.config.workingDir is not None:
            os.chdir(self.config.workingDir)
        self.createTests()
        
    def createTests(self):
        """Create the tests to run. Default behavior is to discover
        tests using TestCollector using nose.loader.TestLoader as the
        test loader.
        """
        log.debug("createTests called")
        if self.suite is not None:
            # We were given an explicit suite to run. Make sure it's
            # loaded and wrapped correctly.
            self.test = self.testLoader.suiteClass(self.suite)
        else:
            self.test = self.testLoader.loadTestsFromNames(self.testNames)

    def runTests(self):
        """Run Tests. Returns true on success, false on failure, and sets
        self.success to the same value.
        """
        log.debug("runTests called")
        if self.testRunner is None:
            self.testRunner = TextTestRunner(stream=self.config.stream,
                                             verbosity=self.config.verbosity,
                                             config=self.config)
        plug_runner = self.config.plugins.prepareTestRunner(self.testRunner)
        if plug_runner is not None:
            self.testRunner = plug_runner
        result = self.testRunner.run(self.test)
        self.success = result.wasSuccessful()
        if self.exit:
            sys.exit(not self.success)
        return self.success

    def showPlugins(self):
        """Print list of available plugins.
        """
        import textwrap

        class DummyParser:
            def __init__(self):
                self.options = []
            def add_option(self, *arg, **kw):
                self.options.append((arg, kw.pop('help', '')))
        
        v = self.config.verbosity
        self.config.plugins.sort()
        for p in self.config.plugins:            
            print "Plugin %s" % p.name
            if v >= 2:
                print "  score: %s" % p.score
                print '\n'.join(textwrap.wrap(p.help().strip(),
                                              initial_indent='  ',
                                              subsequent_indent='  '))
                if v >= 3:
                    print
                    print "  Options:"
                    parser = DummyParser()
                    p.addOptions(parser)
                    for opts, help in parser.options:
                        print '  %s' % (', '.join(opts))
                        if help:
                            print '\n'.join(
                                textwrap.wrap(help.strip(),
                                              initial_indent='    ',
                                              subsequent_indent='    '))
                print
# backwards compatibility
run_exit = main = TestProgram


def run(*arg, **kw):
    """Collect and run test, returning success or failure.
    """
    kw['exit'] = False
    return TestProgram(*arg, **kw).success


def runmodule(name='__main__'):
    """Collect and run tests in a single module only. Defaults to running
    tests in __main__.
    """
    main(defaultTest=name)    


def collector():
    """TestSuite replacement entry point. Use anywhere you might use a
    unittest.TestSuite. The collector will, by default, load options from
    all config files and execute loader.loadTestsFromNames() on the
    configured testNames, or '.' if no testNames are configured.
    """
    # plugins that implement any of these methods are disabled, since
    # we don't control the test runner and won't be able to run them
    setuptools_incompat = ('report', 'finalize', 'prepareTest',
                           'prepareTestLoader', 'prepareTestRunner',
                           'setOutputStream')
    
    conf = Config(files=all_config_files(),
                  plugins=RestrictedPluginManager(exclude=setuptools_incompat))
    conf.configure(argv=['collector'])
    loader = defaultTestLoader(conf)

    if conf.testNames:
        return loader.loadTestsFromNames(conf.testNames)
    else:
        return loader.loadTestsFromNames(('.',))


class TestCollector:
    """Main nose test collector.

    .. Note:: This class is deprecated and will be removed in a future release.

    Uses a test loader to load tests from the directory given in conf
    (conf.path). Uses the default test loader from nose.loader by
    default. Any other loader may be used so long as it implements
    loadTestsFromDir().
    """
    def __init__(self, conf, loader=None):
        warn("TestCollector is deprecated and will be removed in the"
             "next release of nose. "
             "Use `nose.loader.TestLoader.loadTestsFromNames` instead",
             DeprecationWarning)
    
        if loader is None:
            loader = defaultTestLoader(conf)
        self.conf = conf
        self.loader = loader
        self.path = conf.where
        
    def loadtests(self):
        path = tolist(self.path)
        return self.loader.loadTestsFromNames(path)
            
    def __repr__(self):
        return "collector in %s" % self.path
    __str__ = __repr__
    
defaultTestCollector = TestCollector


if __name__ == '__main__':
    main()
