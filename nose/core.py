"""Implements nose test program and collector.
"""
from __future__ import generators

import logging
import os
import re
import sys
import types
import unittest
from optparse import OptionParser
from warnings import warn
import ConfigParser

from nose.plugins import load_plugins, call_plugins
from nose.result import start_capture, end_capture, TextTestResult
from nose.config import Config
from nose.loader import defaultTestLoader
from nose.proxy import ResultProxySuite
from nose.result import Result
from nose.suite import LazySuite, TestModule
from nose.util import absdir, tolist
from nose.importer import add_path

log = logging.getLogger('nose.core')
compat_24 = sys.version_info >= (2, 4)

class TestCollector(LazySuite):
    """Main nose test collector.

    Uses a test loader to load tests from the directory given in conf
    (conf.path). Uses the default test loader from nose.loader by
    default. Any other loader may be used so long as it implements
    loadTestsFromDir().    
    """    
    def __init__(self, conf, loader=None):
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
                 conf=None):
        unittest.TextTestRunner.__init__(self, stream, descriptions, verbosity)
        self.conf = conf
    
    def _makeResult(self):
        return TextTestResult(self.stream,
                              self.descriptions,
                              self.verbosity,
                              self.conf)

    def run(self, test):
        wrapper = call_plugins(self.conf.plugins, 'prepareTest', test)
        if wrapper is not None:
            test = wrapper
        
        # plugins can decorate or capture the output stream
        wrapped = call_plugins(self.conf.plugins, 'setOutputStream',
                               self.stream)
        if wrapped is not None:
            self.stream = wrapped
            
        result = unittest.TextTestRunner.run(self, test)
        call_plugins(self.conf.plugins, 'finalize', result)
        return result

    
class TestProgram(unittest.TestProgram):
    r"""usage: %prog [options] [names]
    
    nose provides an alternate test discovery and running process for
    unittest, one that is intended to mimic the behavior of py.test as much as
    is reasonably possible without resorting to magic.
    
    nose collects tests automatically from python source files,
    directories and packages found in its working directory (which
    defaults to the current working directory). Any python source file,
    directory or package that matches the testMatch regular expression
    (by default: (?:^|[\b_\.-])[Tt]est) will be collected as a test (or
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

    Configuration
    -------------

    In addition to passing command-line options, you may also put configuration
    options in a .noserc or nose.cfg file in your home directory. These are
    standard .ini-style config files. Put your nosetests configuration in a
    [nosetests] section, with the -- prefix removed:

      [nosetests]
      verbosity=3
      with-doctest

    All configuration files that are found will be loaded and their options
    combined.
    """
    verbosity = 1
    userConfigFiles = [
        # Linux users will prefer this
        "~/.noserc",
        # Windows users will prefer this
        "~/nose.cfg",
    ]

    def __init__(self, module=None, defaultTest=defaultTestCollector,
                 argv=None, testRunner=None, testLoader=None, env=None,
                 stream=sys.stderr):
        self.testRunner = testRunner
        self.testCollector = defaultTest
        self.testLoader = testLoader
        self.stream = stream
        self.success = False
        self.module = module

        if not callable(self.testCollector):
            raise ValueError("TestProgram argument defaultTest must be "
                             "a callable with the same signature as "
                             "nose.TestCollector")
        
        if argv is None:
            argv = sys.argv
        if env is None:
            env = os.environ
        okFiles = self.parseUserConfig(argv,
            map(os.path.expanduser, self.userConfigFiles))
        self.parseArgs(argv, env)
        # Log after logging was configured (in self.parseArgs)
        if okFiles:
            log.info("Configuration was read from the following files: %s",
                ", ".join(okFiles))
        elif compat_24:
            log.info("No user configuration found")
        self.createTests()
        self.runTests()
        
    def parseArgs(self, argv, env):
        """Parse argv and env and configure running environment.
        """
        self.conf = configure(argv, env)
        # append the requested module to the list of tests to run
        if self.module:
            try:
                self.conf.tests.append(self.module.__name__)
            except AttributeError:
                self.conf.tests.append(str(self.module))

    def parseUserConfig(self, argv, confFiles):
        """Parse user configuration from supplied confFiles.
        Found configuration options are inserted at the beginning of argv.
        Returns the list of successful config files.
        """
        # XXX Can't do it at top because of recursive imports.
        # These utility functions should be moved to another module however.
        from nose.commands import flag, _bool, option_blacklist
        c = ConfigParser.ConfigParser()
        try:
            okFiles = c.read(confFiles)
        except ConfigParser.Error, e:
            # log not configured yet
            warn("Error in configuration file: \n%s" % e,
                 RuntimeWarning)
            return []
        if compat_24 and not okFiles:
            return []
        sectionName = "nosetests"
        if sectionName not in c.sections():
            # log not configured yet
            warn("Configuration files lack a 'nosetests' section",
                 RuntimeWarning)
            return []
        confArgv = []
        for optionName in c.options(sectionName):
            if optionName in option_blacklist:
                continue
            value = c.get(sectionName, optionName)
            if value:
                if flag(value):
                    if _bool(value):
                        confArgv.append('--' + optionName)
                else:
                    confArgv.append('--' + optionName)
                    confArgv.append(value)
        # Insert in-place, after the program name but before other options
        argv[1:1] = confArgv
        return okFiles

    def createTests(self):
        """Create the tests to run. Default behavior is to discover
        tests using TestCollector using nose.loader.TestLoader as the
        test loader.
        """
        self.test = self.testCollector(self.conf, self.testLoader)

    def runTests(self):
        """Run Tests. Returns true on success, false on failure, and sets
        self.success to the same value.
        """
        if self.testRunner is None:
            self.testRunner = TextTestRunner(stream=self.stream,
                                             verbosity=self.conf.verbosity,
                                             conf=self.conf)
        result = self.testRunner.run(self.test)
        self.success = result.wasSuccessful()
        return self.success

def get_parser(env=None, builtin_only=False, doc=None):
    if doc is None:
        doc = TestProgram.__doc__
    parser = OptionParser(doc)
    parser.add_option("-V","--version",action="store_true",
                      dest="version",default=False,
                      help="Output nose version and exit")
    parser.add_option("-v", "--verbose",
                      action="count", dest="verbosity",
                      default=int(env.get('NOSE_VERBOSE', 1)),
                      help="Be more verbose. [NOSE_VERBOSE]")
    parser.add_option("--verbosity", action="store", dest="verbosity",
                      type="int", help="Set verbosity; --verbosity=2 is "
                      "the same as -vv")
    parser.add_option("-l", "--debug", action="store",
                      dest="debug", default=env.get('NOSE_DEBUG'),
                      help="Activate debug logging for one or more systems. "
                      "Available debug loggers: nose, nose.importer, "
                      "nose.inspector, nose.plugins, nose.result and "
                      "nose.selector. Separate multiple names with a comma.")
    parser.add_option("--debug-log", dest="debug_log", action="store",
                      default=env.get('NOSE_DEBUG_LOG'),
                      help="Log debug messages to this file "
                      "(default: sys.stderr)")
    parser.add_option("-q", "--quiet", action="store_const",
                      const=0, dest="verbosity")
    parser.add_option("-w", "--where", action="append", dest="where",
                      help="Look for tests in this directory [NOSE_WHERE]")
    parser.add_option("-e", "--exclude", action="append", dest="exclude",
                      help="Don't run tests that match regular "
                      "expression [NOSE_EXCLUDE]")
    parser.add_option("-i", "--include", action="append", dest="include",
                      help="Also run tests that match regular "
                      "expression [NOSE_INCLUDE]")
    parser.add_option("-m", "--match", "--testmatch", action="store",
                      dest="test_match", help="Use this regular expression to "
                      "find tests [NOSE_TESTMATCH]",
                      default=env.get('NOSE_TESTMATCH'))
    parser.add_option("-s", "--nocapture", action="store_false",
                      default=not env.get('NOSE_NOCAPTURE'), dest="capture",
                      help="Don't capture stdout (any stdout output "
                      "will be printed immediately) [NOSE_NOCAPTURE]")
    parser.add_option("-d", "--detailed-errors", action="store_true",
                      default=env.get('NOSE_DETAILED_ERRORS'),
                      dest="detailedErrors", help="Add detail to error"
                      " output by attempting to evaluate failed"
                      " asserts [NOSE_DETAILED_ERRORS]")
    parser.add_option("--pdb", action="store_true", dest="debugErrors",
                      default=env.get('NOSE_PDB'), help="Drop into debugger "
                      "on errors")
    parser.add_option("--pdb-failures", action="store_true",
                      dest="debugFailures",
                      default=env.get('NOSE_PDB_FAILURES'),
                      help="Drop into debugger on failures")
    parser.add_option("-x", "--stop", action="store_true", dest="stopOnError",
                      default=env.get('NOSE_STOP'),
                      help="Stop running tests after the first error or "
                      "failure")
    parser.add_option("-P", "--no-path-adjustment", action="store_false",
                      dest="addPaths",
                      default=not env.get('NOSE_NOPATH'),
                      help="Don't make any changes to sys.path when "
                      "loading tests [NOSE_NOPATH]")
    parser.add_option("--exe", action="store_true", dest="includeExe",
                      default=env.get('NOSE_INCLUDE_EXE',
                                      sys.platform=='win32'),
                      help="Look for tests in python modules that are "
                      "executable. Normal behavior is to exclude executable "
                      "modules, since they may not be import-safe "
                      "[NOSE_INCLUDE_EXE]")
    parser.add_option("--noexe", action="store_false", dest="includeExe",
                      help="DO NOT look for tests in python modules that are "
                      "executable. (The default on the windows platform is to "
                      "do so.)")
    
    # add opts from plugins
    all_plugins = []
    # when generating the help message, load only builtin plugins
    for plugcls in load_plugins(others=not builtin_only):
        plug = plugcls()
        try:
            plug.add_options(parser, env)
        except AttributeError:
            pass
    
    return parser

def configure(argv=None, env=None, help=False, disable_plugins=None):
    """Configure the nose running environment. Execute configure before
    collecting tests with nose.TestCollector to enable output capture and
    other features.
    """
    if argv is None:
        argv = sys.argv
    if env is None:
        env = os.environ
    
    conf = Config()
    parser = get_parser(env=env, builtin_only=help)
        
    options, args = parser.parse_args(argv)
    if help:
        return parser.format_help()
    
    try:
        log.debug('Adding %s to tests to run' % args[1:])
        conf.tests.extend(args[1:])
    except IndexError:
        pass
    
    if options.version:
        from nose import __version__
        print "%s version %s" % (os.path.basename(sys.argv[0]), __version__)
        sys.exit(0)

    # where is an append action, so it can't have a default value 
    # in the parser, or that default will always be in the list
    if not options.where:
        options.where = env.get('NOSE_WHERE', os.getcwd())

    # include and exclude also
    if not options.include:
        options.include = env.get('NOSE_INCLUDE', [])
    if not options.exclude:
        options.exclude = env.get('NOSE_EXCLUDE', [])
        
    configure_logging(options)

    # hand options to plugins
    all_plugins = [plug() for plug in load_plugins()]
    for plug in all_plugins:
        plug.configure(options, conf)
        if plug.enabled and disable_plugins:
            for meth in disable_plugins:
                if hasattr(plug, meth):
                    plug.enabled = False
                    log.warning("Plugin %s disabled: not all methods "
                                "supported in this environment" % plug.name)
    conf.addPaths = options.addPaths
    conf.capture = options.capture
    conf.detailedErrors = options.detailedErrors
    conf.debugErrors = options.debugErrors
    conf.debugFailures = options.debugFailures
    conf.plugins = [ plug for plug in all_plugins if plug.enabled ]
    conf.stopOnError = options.stopOnError
    conf.verbosity = options.verbosity
    conf.includeExe = options.includeExe
    
    if options.where is not None:
        conf.where = []
        for path in tolist(options.where):
            log.debug('Adding %s as nose working directory', path)
            abs_path = absdir(path)
            if abs_path is None:
                raise ValueError("Working directory %s not found, or "
                                 "not a directory" % path)
            conf.where.append(abs_path)
            log.info("Looking for tests in %s", abs_path)
            if conf.addPaths and \
                    os.path.exists(os.path.join(abs_path, '__init__.py')):
                log.info("Working directory %s is inside of a package; "
                         "adding package root to sys.path" % abs_path)
                add_path(abs_path)
                
    if options.include:
        conf.include = map(re.compile, tolist(options.include))
        log.info("Including tests matching %s", options.include)
        
    if options.exclude:
        conf.exclude = map(re.compile, tolist(options.exclude))
        log.info("Excluding tests matching %s", options.exclude)

    if options.test_match:
        conf.testMatch = re.compile(options.test_match)
        log.info("Test match regular expression: %s", options.test_match)
        
    if conf.capture:
        start_capture()
        
    try:
        # give plugins a chance to start
        call_plugins(conf.plugins, 'begin')
    except:
        if conf.capture:
            end_capture()
        raise
    return conf

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
        lvl = 1
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
    result = TestProgram(*arg, **kw).success
    end_capture()
    return result

def runmodule(name='__main__'):
    """Collect and run tests in a single module only. Defaults to running
    tests in __main__.
    """
    conf = configure()
    testLoader = defaultTestLoader(conf)
    def collector(conf, loader):
        return TestModule(loader.loadTestsFromModule, conf, name)
    main(defaultTest=collector, testLoader=testLoader)    

if __name__ == '__main__':
    main()
