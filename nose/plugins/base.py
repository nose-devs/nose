import os
import re
import textwrap
from optparse import OptionConflictError
from warnings import warn
from nose.util import tolist

class Plugin(object):
    """Base class for nose plugins. It's not *necessary* to subclass this
    class to create a plugin; however, all plugins must implement
    `add_options(self, parser, env)` and `configure(self, options,
    conf)`, and must have the attributes `enabled` and `name`.

    Plugins should not be enabled by default.

    Subclassing Plugin will give your plugin some friendly default
    behavior:

      * A --with-$name option will be added to the command line
        interface to enable the plugin. The plugin class's docstring
        will be used as the help for this option.
      * The plugin will not be enabled unless this option is selected by
        the user.    
    """
    can_configure = False
    enabled = False
    enableOpt = None
    name = None
    score = 100

    def __init__(self):
        if self.name is None:
            self.name = self.__class__.__name__.lower()
        if self.enableOpt is None:
            self.enableOpt = "enable_plugin_%s" % self.name
            
    def addOptions(self, parser, env=os.environ):
        """Add command-line options for this plugin.

        The base plugin class adds --with-$name by default, used to enable the
        plugin. 
        """
        self.add_options(parser, env)
        
    def add_options(self, parser, env=os.environ):
        """Non-camel-case version of func name for backwards compatibility.
        """
        # FIXME raise deprecation warning if wasn't called by wrapper 
        try:
            self.options(parser, env)
            self.can_configure = True
        except OptionConflictError, e:
            warn("Plugin %s has conflicting option string: %s and will "
                 "be disabled" % (self, e), RuntimeWarning)
            self.enabled = False
            self.can_configure = False
            
    def options(self, parser, env=os.environ):
        """New plugin API: override to just set options. Use instead
        of add_options.
        """
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')
        parser.add_option("--with-%s" % self.name,
                          action="store_true",
                          dest=self.enableOpt,
                          default=env.get(env_opt),
                          help="Enable plugin %s: %s [%s]" %
                          (self.__class__.__name__, self.help(), env_opt))

    def configure(self, options, conf):
        """Configure the plugin and system, based on selected options.

        The base plugin class sets the plugin to enabled if the enable option
        for the plugin (self.enableOpt) is true.
        """
        if not self.can_configure:
            return
        self.conf = conf
        if hasattr(options, self.enableOpt):
            self.enabled = getattr(options, self.enableOpt)

    def help(self):
        """Return help for this plugin. This will be output as the help
        section of the --with-$name option that enables the plugin.
        """
        if self.__class__.__doc__:
            # doc sections are often indented; compress the spaces
            return textwrap.dedent(self.__class__.__doc__)
        return "(no help available)"

    # Compatiblity shim
    def tolist(self, val):
        from warnings import warn
        warn("Plugin.tolist is deprecated. Use nose.util.tolist instead",
             DeprecationWarning)
        return tolist(val)


class IPluginInterface(object):
    """
    Nose plugin API
    ---------------

    While it is recommended that plugins subclass
    nose.plugins.Plugin, the only requirements for a plugin are
    that it implement the methods `add_options(self, parser, env)` and
    `configure(self, options, conf)`, and have the attributes
    `enabled` and `name`. 
    
    Plugins may implement any or all of the methods documented
    below. Please note that they *must not* subclass PluginInterface;
    PluginInterface is a only description of the plugin API.

    When plugins are called, the first plugin that implements a method
    and returns a non-None value wins, and plugin processing ends. The
    exceptions to this are `loadTestsFromModule`, `loadTestsFromName`,
    and `loadTestsFromPath`, which allow multiple plugins to load and
    return tests.

    In general, plugin methods correspond directly to methods of
    nose.selector.Selector, nose.loader.TestLoader and
    nose.result.TextTestResult are called by those methods when they are
    called. In some cases, the plugin hook doesn't neatly match the
    method in which it is called; for those, the documentation for the
    hook will tell you where in the test process it is called.

    Plugin hooks fall into two broad categories: selecting and loading
    tests, and watching and reporting on test results.
    
    Selecting and loading tests
    ===========================

    To alter test selection behavior, implement any necessary `want*`
    methods as outlined below. Keep in mind, though, that when your
    plugin returns True from a `want*` method, you will send the requested
    object through the normal test collection process. If the object
    represents something from which normal tests can't be collected, you
    must also implement a loader method to load the tests.

    Examples:
    
     * The builtin doctests plugin, for python 2.4 only, implements
       `wantFile` to enable loading of doctests from files that are not
       python modules. It also implements `loadTestsFromModule` to load
       doctests from python modules, and `loadTestsFromPath` to load tests
       from the non-module files selected by `wantFile`.
       
     * The builtin attrib plugin implements `wantFunction` and
       `wantMethod` so that it can reject tests that don't match the
       specified attributes.
    
    Watching or reporting on tests
    ==============================

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
    """
    def __new__(cls, *arg, **kw):
        raise TypeError("IPluginInterface class is for documentation only")

    def addOptions(self, parser, env=os.environ):
        """Called to allow plugin to register command line
        options with the parser.

        Do *not* return a value from this method unless you want to stop
        all other plugins from setting their options.

        DEPRECATED
        """
        pass
    add_options = addOptions

    def addDeprecated(self, test):
        """Called when a deprecated test is seen. DO NOT return a value
        unless you want to stop other plugins from seeing the deprecated
        test.

        DEPRECATED

        Parameters:
         * test:
           the test case 
        """
        pass
    addDeprecated.deprecated = True

    def addError(self, test, err):
        """Called when a test raises an uncaught exception. DO NOT return a
        value unless you want to stop other plugins from seeing that the
        test has raised an error.

        Parameters:
         * test:
           the test case
         * err:
           sys.exc_info() tuple
         * capt:
           Captured output, if any
           DEPRECATED: this parameter will not be passed
        """
        pass
    addError.changed = True

    def addFailure(self, test, err):
        """Called when a test fails. DO NOT return a value unless you
        want to stop other plugins from seeing that the test has failed.

        Parameters:
         * test:
           the test case
         * err:
           sys.exc_info() tuple
         * capt:
           Captured output, if any.
           DEPRECATED: this parameter will not be passed
         * tb_info:
           Introspected traceback info, if any
           DEPRECATED: this parameter will not be passed
        """
        pass
    addFailure.changed = True

    def addSkip(self, test):
        """Called when a test is skipped. DO NOT return a value unless
        you want to stop other plugins from seeing the skipped test.

        DEPRECATED

        Parameters:
         * test:
           the test case
        """
        pass
    addSkip.deprecated = True

    def addSuccess(self, test, capt):
        """Called when a test passes. DO NOT return a value unless you
        want to stop other plugins from seeing the passing test.

        Parameters:
         * test:
           the test case
         * capt:
           Captured output, if any.
        """
        pass        

    def afterDirectory(self, path):
        """Called after all tests have been loaded from directory at path
        and run.

        Parameters:
         * path
           the directory that has finished processing
        """
        pass
    afterDirectory._new = True

    def afterImport(self, filename, module):
        """Called after module is imported from filename. afterImport
        is called even if the import failed.

        Parameters:
         * filename:
           The file that was loaded
         * module:
           The name of the module
        """
        pass
    afterImport._new = True        

    def afterTest(self, test):
        """Called after the test has been run and the result recorded
        (after stopTest).

        Parameters:
         * test:
           test test case
        """
        pass
    afterTest._new = True

    def beforeDirectory(self, path):
        """Called before tests are loaded from directory at path.

        Parameters:
         * path:
           the directory that is about to be processed
        """
        pass
    beforeDirectory._new = True

    def beforeImport(self, filename, module):
        """Called before module is imported from filename.

        Parameters:
         * filename
           The file that will be loaded
         * module
           The name of the module found in file
        """
    beforeImport._new = True
    
    def beforeTest(self, test):
        """Called before the test is run (before startTest).
        
        Parameters:
         * test:
           the test case
        """        
        pass
    beforeTest._new = True
            
    def begin(self):
        """Called before any tests are collected or run. Use this to
        perform any setup needed before testing begins.
        """
        pass

    def configure(self, options, conf):
        """Called after the command line has been parsed, with the
        parsed options and the config container. Here, implement any
        config storage or changes to state or operation that are set
        by command line options.

        Do *not* return a value from this method unless you want to
        stop all other plugins from being configured.
        """
        pass

    def finalize(self, result):
        """Called after all report output, including output from all plugins,
        has been sent to the stream. Use this to print final test
        results. Return None to allow other plugins to continue
        printing, any other value to stop them.
        """
        pass

    def describeTest(self, test):
        """Return a test description. Called by test.shortDescription.

        Parameters:
         * test:
           the test case
        """
        pass
    describeTest._new = True

    def formatError(self, test, err):
        """Called in result.addError, before plugin.addError. If you
        want to replace or modify the error tuple, return a new error
        tuple.

        Parameters:
         * test:
           the test case
         * err:
           the error tuple (class, value, traceback)
        """
        pass
    formatError._new = True
    formatError.chainable = True

    def formatFailure(self, test, err):
        """Called in result.addFailure, before plugin.addFailure. If you
        want to replace or modify the error tuple, return a new error
        tuple.

        Parameters:
         * test:
           the test case
         * err:
           the error tuple (class, value, traceback)
        """
        pass
    formatFailure._new = True
    formatFailure.chainable = True

    def handleError(self, test, err):
        """Called on addError. To handle the error yourself and prevent normal
        error processing, return a true value.

        Parameters:
         * test:
           the test case
         * err:
           the error tuple (class, value, traceback)
        """
        pass
    handleError._new = True

    def handleFailure(self, test, err):
        """Called on addFailure. To handle the failure yourself and
        prevent normal failure processing, return a true value.

        Parameters:
         * test:
           the test case
         * err:
           the error tuple (class, value, traceback)
        """
        pass
    handleFailure._new = True

    # FIXME loadTestsFromClass, loadTestsFromDir
    def loadTestsFromDir(self, path):
        """Return iterable of tests from a directory. May be a
        generator.  Each item returned must be a runnable
        unittest.TestCase (or subclass) instance or suite instance.
        Return None if your plugin cannot collect any tests from
        module.

        Parameters:
         * path:
           The path to the directory.
        """
        pass
    loadTestsFromDir.generative = True
    loadTestsFromDir._new = True
    
    def loadTestsFromModule(self, module):
        """Return iterable of tests in a module. May be a
        generator. Each item returned must be a runnable
        unittest.TestCase (or subclass) instance.
        Return None if your plugin cannot
        collect any tests from module.

        Parameters:
         * module:
           The module object
        """
        pass
    loadTestsFromModule.generative = True
    
    def loadTestsFromName(self, name, module=None, importPath=None):
        """Return tests in this file or module. Return None if you are not able
        to load any tests, or an iterable if you are. May be a
        generator.

        Parameters:
         * name:
           The test name. May be a file or module name plus a test
           callable. Use split_test_name to split into parts.
         * module:
           Module from which the name is to be loaded
         * importPath:
           Path from which file (must be a python module) was found
           DEPRECATED: this argument will NOT be passed.
        """
        pass
    loadTestsFromName.generative = True

    def loadTestsFromNames(self, names, module=None):
        """Return a tuple of (tests loaded, remaining names). Return
        None if you are not able to load any tests. Multiple plugins
        may implement loadTestsFromNames; the remaining name list from
        each will be passed to the next as input.

        Parameters:
         * names:
           List of test names.
         * module:
           Module from which the names are to be loaded
        """
        pass
    loadTestsFromNames._new = True
    loadTestsFromNames.chainable = True

    def loadTestsFromPath(self, path, module=None, importPath=None):
        """Return tests in this file or directory. Return None if you are not
        able to load any tests, or an iterable if you are. May be a
        generator.

        Parameters:
         * path:
           The full path to the file or directory.
         * module:
           Module in which the file/dir is found
         * importPath:
           Path from which file (must be a python module) was found        
        """
        pass
    loadTestsFromPath.generative = True
    loadTestsFromFile = loadTestsFromPath
    
    def loadTestsFromTestCase(self, cls):
        """Return tests in this test case class. Return None if you are
        not able to load any tests, or an iterable if you are. May be a
        generator.

        DEPRECATE?

        Parameters:
         * cls:
           The test case class
        """
        pass
    loadTestsFromTestCase.generative = True

    def loadTestsFromTestClass(self, cls):
        """Return tests in this test class. Class will *not* be a
        unittest.TestCase subclass. Return None if you are not able to
        load any tests, an iterable if you are. May be a generator.

        Parameters:
         * cls:
           The test class
        """
        pass
    loadTestsFromTestClass._new = True
    loadTestsFromTestClass.generative = True

    def makeTest(self, obj, parent):
        """Given an object and its parent, return a test case. Must be
        a unittest.TestCase or TestSuite (or subclass) instance. This
        is called before default test loading to allow plugins to load
        an alternate test case or cases for an object. May be a generator.

        Parameters:
         * obj:
           The object to be made into a test
         * parent:
           The parent of obj (eg, for a method, the class)
         """
        pass
    makeTest._new = True
    makeTest.generative = True

    def prepareTest(self, test):
        """Called before the test is run by the test runner. Please
        note the article *the* in the previous sentence: prepareTest
        is called *only once*, and is passed the test case or test
        suite that the test runner will execute. It is *not* called
        for each individual test case. If you return a non-None value,
        that return value will be run as the test. Use this hook to
        wrap or decorate the test with another function. If you need
        to modify or wrap individual test cases, use `prepareTestCase`
        instead.

        Parameters:
         * test:
           the test case
        """
        pass

    def prepareTestCase(self, test):
        """Prepare or wrap an individual test case. Called before
        execution of the test. The test passed here is a
        nose.case.Test instance; the case to be executed is in the
        test attribute of the passed case. To modify the test to be
        run, you should return a callable that takes one argument (the
        test result object) -- it is recommended that you *do not*
        side-effect the nose.case.Test instance you have been passed.

        Keep in mind that when you replace the test callable you are
        replacing the run() method of the test case -- including the
        exception handling and result calls, etc.

        Parameters:
         * test:
           the test case
        """
        pass
    
    def prepareTestLoader(self, loader):
        """Called before tests are loaded. To replace the test loader,
        return a test loader. To allow other plugins to process the
        test loader, return None. Only one plugin may replace the test
        loader. Only valid when using nose.TestProgram.

        Parameters:
         * loader:
           the test loader
        """
        pass
    prepareTestLoader._new = True

    def prepareTestResult(self, result):
        """Called before the first test is run. To use a different
        test result handler for all tests than the given result,
        return a test result handler. NOTE however that this handler
        will only be seen by tests, that is, inside of the result
        proxy system. The TestRunner and TestProgram -- whether nose's
        or other -- will continue to see the original result
        handler. For this reason, it is usually better to monkeypatch
        the result (for instance, if you want to handle TODO
        exceptions in some way). Only one plugin may replace the
        result, but many may monkeypatch it. If you want to
        monkeypatch and stop other plugins from doing so, monkeypatch
        and return the patched result.

        Parameters:
         * result:
           the test result
        """
        pass
    prepareTestResult._new = True

    def prepareTestRunner(self, runner):
        """Called before tests are run. To replace the test runner,
        return a test runner. To allow other plugins to process the
        test runner, return None. Only valid when using nose.TesrProgram.

        Parameters:
         * runner
           the test runner
        """
        pass
    prepareTestRunner._new = True
        
    def report(self, stream):
        """Called after all error output has been printed. Print your
        plugin's report to the provided stream. Return None to allow
        other plugins to print reports, any other value to stop them.

        Parameters:
         * stream:
           stream object; send your output here
        """
        pass

    def setOutputStream(self, stream):
        """Called before test output begins. To direct test output to a
        new stream, return a stream object, which must implement a
        `write(msg)` method. If you only want to note the stream, not
        capture or redirect it, then return None.

        Parameters:
         * stream:
           the original output stream
        """
    
    def startTest(self, test):
        """Called before each test is run. DO NOT return a value unless
        you want to stop other plugins from seeing the test start.

        Parameters:
         * test:
           the test case
        """
        pass
    
    def stopTest(self, test):
        """Called after each test is run. DO NOT return a value unless
        you want to stop other plugins from seeing that the test has stopped.

        Parameters:
         * test:
           the test case
        """
        pass

    def testName(self, test):
        """Return a short test name. Called by test.__str__.

        Parameters:
         * test:
           the test case
        """
        pass
    testName._new = True

    def wantClass(self, cls):
        """Return true if you want the main test selector to collect
        tests from this class, false if you don't, and None if you don't
        care.

        Parameters:
         * cls:
           The class
        """
        pass
    
    def wantDirectory(self, dirname):
        """Return true if you want test collection to descend into this
        directory, false if you do not, and None if you don't care.

        Parameters:
         * dirname:
           Full path to directory
        """
        pass
    
    def wantFile(self, file):
        """Return true if you want to collect tests from this file,
        false if you do not and None if you don't care.

        Change from 0.9: The optional package parameter is no longer passed.

        Parameters:
         * file:
           Full path to file
        """
        pass
    
    def wantFunction(self, function):
        """Return true to collect this function as a test, false to
        prevent it from being collected, and None if you don't care.

        Parameters:
         * function:
           The function object
        """
        pass
    
    def wantMethod(self, method):
        """Return true to collect this method as a test, false to
        prevent it from being collected, and None if you don't care.

        Parameters:
         * method:
           The method object
        """    
        pass
    
    def wantModule(self, module):
        """Return true if you want to collection to descend into this
        module, false to prevent the collector from descending into the
        module, and None if you don't care.

        Parameters:
         * module:
           The module object
        """
        pass
    
    def wantModuleTests(self, module):
        """Return true if you want the standard test loader to load
        tests from this module, false if you want to prevent it from
        doing so, and None if you don't care. DO NOT return true if your
        plugin will be loading the tests itself!

        Parameters:
         * module:
           The module object
        """
        pass
    
