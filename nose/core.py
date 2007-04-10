"""Implements nose test program and collector.
"""
import logging
import os
import re
import sys
import types
import unittest
from inspect import isclass


from nose.config import Config
from nose.importer import add_path
from nose.loader import defaultTestLoader
from nose.plugins.manager import DefaultPluginManager
from nose.result import TextTestResult
from nose.util import absdir, tolist


log = logging.getLogger('nose.core')


class TestCollector:
    """Main nose test collector.

    Uses a test loader to load tests from the directory given in conf
    (conf.path). Uses the default test loader from nose.loader by
    default. Any other loader may be used so long as it implements
    loadTestsFromDir().    
    """
    def __init__(self, conf, loader=None):
        raise NotImplentedError("TestCollector not yet reimplemented")
    
        if loader is None:
            loader = defaultTestLoader(conf)
        self.conf = conf
        self.loader = loader
        self.path = conf.where
        
    def loadtests(self):
        for path in tolist(self.path):
            for test in self.loader.loadTestsFromDir(path):
                yield test
            
    def __repr__(self):
        return "collector in %s" % self.path
    __str__ = __repr__
    
defaultTestCollector = TestCollector


def collector():
    """TestSuite replacement entry point. Use anywhere you might use a
    unittest.TestSuite. Note: Except with testoob; currently (nose 0.9)
    testoob's test loading is not compatible with nose's collector
    implementation.

    Returns a TestCollector configured to use a TestLoader that returns
    ResultProxySuite test suites, which use a proxy result object to
    enable output capture and assert introspection.
    """
    raise NotImplementedError("collector() not yet reimplemented")
    # plugins that implement any of these methods are disabled, since
    # we don't control the test runner and won't be able to run them
    setuptools_incompat = ( 'finalize', 'prepareTest', 'report',
                            'setOutputStream')
    
    conf = configure(argv=[], env=os.environ,
                     disable_plugins=setuptools_incompat)
    Result.conf = conf
    loader = defaultTestLoader(conf)
    loader.suiteClass = ResultProxySuite
    return TestCollector(conf, loader)

            
class TextTestRunner(unittest.TextTestRunner):
    """Test runner that uses nose's TextTestResult to enable output
    capture and assert introspection, as well as providing hooks for
    plugins to override or replace the test output stream, results, and
    the test case itself.
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
        wrapper = self.config.plugins.prepareTest(test)
        if wrapper is not None:
            test = wrapper
        
        # plugins can decorate or capture the output stream
        wrapped = self.config.plugins.setOutputStream(self.stream)
        if wrapped is not None:
            self.stream = wrapped
            
        result = unittest.TextTestRunner.run(self, test)
        self.config.plugins.finalize(result)
        return result

    
class TestProgram(unittest.TestProgram):
    """usage: %prog [options] [names]
    
    nose provides an alternate test discovery and running process for
    unittest, one that is intended to mimic the behavior of py.test as much as
    is reasonably possible without resorting to magic.
    
    nose collects tests automatically from python source files,
    directories and packages found in its working directory (which
    defaults to the current working directory). Any python source file,
    directory or package that matches the testMatch regular expression
    (by default: (?:^|[\\b_\\.-])[Tt]est) will be collected as a test (or
    source for collection of tests). In addition, all other packages
    found in the working directory are examined for python source files
    or directories that match testMatch. Package discovery descends all
    the way down the tree, so package.tests and package.sub.tests and
    package.sub.sub2.tests will all be collected.
    
    Within a test directory or package, any python source file matching
    testMatch will be examined for test cases. Within a test file,
    functions and classes whose names match testMatch and TestCase
    subclasses with any name will be loaded and executed as tests. Tests
    may use the assert keyword or raise AssertionErrors to indicate test
    failure. TestCase subclasses may do the same or use the various
    TestCase methods available.

    Tests may raise nose.SkipTest to indicate that they should be
    skipped or nose.DeprecatedTest to indicate that they are
    deprecated. Skipped and deprecated tests do not count as failures,
    but details on them are printed at the end of the test run along
    with any failures and errors.
        
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
      
    Note however that specifying a test name will *not* cause nose to run
    a test that it does not discover. Test names specified are compared
    against tests discovered, and only the requested tests are
    run. Setup and teardown methods are run at all stages. That means
    that if you run:

      %prog some.tests.test_module:test_function

    And have defined setup or teardown methods in tests and test_module,
    those setup methods will run before the test_function test, and
    teardown after, just as if you were running all tests.

    You may also change the working directory where nose looks for tests,
    use the -w switch:

      %prog -w /path/to/tests

    Further customization of test selection and loading is possible
    through the use of plugins.

    Test result output is identical to that of unittest, except for the
    additional features (output capture, assert introspection, and any plugins
    that control or produce output) detailed in the options below.
    """
    verbosity = 1

    def __init__(self, module=None, defaultTest='.', argv=None,
                 testRunner=None, testLoader=None, env=None, config=None):
        if env is None:
            env = os.environ
        if config is None:
            config = Config(env=env, plugins=DefaultPluginManager())
        self.config = config
        unittest.TestProgram.__init__(
            self, module=module, defaultTest=defaultTest,
            argv=argv, testRunner=testRunner, testLoader=testLoader)
        
        
    def parseArgs(self, argv):
        """Parse argv and env and configure running environment.
        """
        log.debug("parseArgs is called %s", argv)

        self.config.configure(argv, doc=TestProgram.__doc__)
        if self.config.options.version:
            from nose import __version__
            print "%s version %s" % (os.path.basename(sys.argv[0]), __version__)
            sys.exit(0)

        log.debug("configured %s", self.config)
        
        # instantiate the test loader
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
        self.createTests()
        
    def createTests(self):
        """Create the tests to run. Default behavior is to discover
        tests using TestCollector using nose.loader.TestLoader as the
        test loader.
        """
        log.debug("createTests called")        
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
        if self.config.exit:
            sys.exit(not self.success)
        return self.success


##     # FIXME move this
##     # add opts from plugins
##     all_plugins = []
##     # when generating the help message, load only builtin plugins
##     for plugcls in load_plugins():
##         plug = plugcls()
##         try:
##             plug.add_options(parser, env)
##         except AttributeError:
##             pass
    



# FIXME use plugin manager
#    try:
#        # give plugins a chance to start
#        call_plugins(conf.plugins, 'begin')
#    except:
#        if conf.capture:
#            end_capture()
#        raise


def configure_logging(options):
    """Configure logging for nose, or optionally other packages. Any logger
    name may be set with the debug option, and that logger will be set to
    debug level and be assigned the same handler as the nose loggers, unless
    it already has a handler.
    """
    format = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
    if options.debug_log:
        handler = logging.FileHandler(options.debug_log)
    else:
        handler = logging.StreamHandler(sys.stderr) # FIXME        
    handler.setFormatter(format)

    logger = logging.getLogger('nose')
    logger.propagate = 0

    # only add our default handler if there isn't already one there
    # this avoids annoying duplicate log messages.
    if not logger.handlers:
        logger.addHandler(handler)
        
    # default level    
    lvl = logging.WARNING
    if options.verbosity >= 5:
        lvl = 0
    elif options.verbosity >= 4:
        lvl = logging.DEBUG
    elif options.verbosity >= 3:
        lvl = logging.INFO
    logger.setLevel(lvl)
        
    # individual overrides
    if options.debug:
        # no blanks
        debug_loggers = [ name for name in options.debug.split(',') if name ]
        for logger_name in debug_loggers:
            l = logging.getLogger(logger_name)
            l.setLevel(logging.DEBUG)
            if not l.handlers and not logger_name.startswith('nose'):
                l.addHandler(handler)
                
            
def main(*arg, **kw):
    """Run and exit with 0 on success or 1 on failure.
    """
    return sys.exit(not run(*arg, **kw))

# backwards compatibility
run_exit = main

def run(*arg, **kw):
    """Collect and run test, returning success or failure
    """
    return TestProgram(*arg, **kw).success

def runmodule(name='__main__'):
    """Collect and run tests in a single module only. Defaults to running
    tests in __main__.
    """
    conf = configure()
    testLoader = defaultTestLoader(conf)
    def collector(conf, loader):
        return loader.loadTestsFromModule(name=name)
    main(defaultTest=collector, testLoader=testLoader)    

if __name__ == '__main__':
    main()
