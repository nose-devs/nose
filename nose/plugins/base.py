import os
import textwrap
from optparse import OptionConflictError
from warnings import warn
from nose.util import tolist

class Plugin(object):
    """Base class for nose plugins. It's not *necessary* to subclass this
    class to create a plugin; however, all plugins must implement
    `options(self, parser, env)` and `configure(self, options,
    conf)`, and must have the attributes `enabled`, `name` and `score`.

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
        """New plugin API: override to just set options. Implement
        this method instead of addOptions or add_options for normal
        options behavior with protection from OptionConflictErrors.
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
    that it implement the methods `options(self, parser, env)` and
    `configure(self, options, conf)`, and have the attributes
    `enabled`, `name` and `score`.
    
    Plugins may implement any or all of the methods documented
    below. Please note that they *must not* subclass `IPluginInterface`;
    `IPluginInterface` is a only description of the plugin API.

    When plugins are called, the first plugin that implements a method
    and returns a non-None value wins, and plugin processing ends. The
    exceptions to this are methods marked as `generative` or
    `chainable`.  `generative` methods combine the output of all
    plugins that respond with an iterable into a single flattened
    iterable response (a generator, really). `chainable` methods pass
    the results of calling plugin A as the input to plugin B, where
    the positions in the chain are determined by the plugin sort
    order, which is in order by `score` descending.

    In general, plugin methods correspond directly to methods of
    `nose.selector.Selector`, `nose.loader.TestLoader` and
    `nose.result.TextTestResult` are called by those methods when they are
    called. In some cases, the plugin hook doesn't neatly match the
    method in which it is called; for those, the documentation for the
    hook will tell you where in the test process it is called.

    Plugin hooks fall into four broad categories: selecting and
    loading tests, handling errors raised by tests, preparing objects
    used in the testing process, and watching and reporting on test
    results.
    
    Selecting and loading tests
    ===========================

    To alter test selection behavior, implement any necessary `want*`
    methods as outlined below. Keep in mind, though, that when your
    plugin returns True from a `want*` method, you will send the requested
    object through the normal test collection process. If the object
    represents something from which normal tests can't be collected, you
    must also implement a loader method to load the tests.

    Examples:
    
    * The builtin doctests plugin implements `wantFile` to enable
      loading of doctests from files that are not python modules. It
      also implements `loadTestsFromModule` to load doctests from
      python modules, and `loadTestsFromFile` to load tests from the
      non-module files selected by `wantFile`.
       
    * The builtin attrib plugin implements `wantFunction` and
      `wantMethod` so that it can reject tests that don't match the
      specified attributes.

    Handling errors
    ===============

    To alter error handling behavior -- for instance to catch a
    certain class of exception and handle it differently from the
    normal error or failure handling -- you should subclass
    `ErrorClassPlugin`. See the documentation for `ErrorClassPlugin`_ for
    more details.

    Examples:

    * The builtin skip and deprecated plugins are ErrorClass plugins.

    Preparing test objects
    ======================

    To alter, get a handle on, or replace test framework objects such
    as the loader, result, runner, and test cases, use the appropriate
    prepare methods. The simplest reason to use prepare is if you need
    to use an object yourself. For example, the isolate plugin
    implements `prepareTestLoader` so that it can use the test loader
    later on to load tests. If you return a value from a prepare
    method, that value will be used in place of the loader, result,
    runner or test case, respectively. When replacing test cases, be
    aware that you are replacing the entire test case -- including the
    whole `run(result)` method of the `unittest.TestCase` -- so if you
    want normal unittest test result reporting, you must implement the
    same calls to result as `unittest.TestCase.run`.

    Examples:

    * The builtin isolate plugin implements `prepareTestLoader` but
      does not replace the test loader.

    * The builtin profile plugin implements `prepareTest` and does
      replace the top-level test case by returning the case wrapped in
      the profiler function.
    
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

        .. Note:: DEPRECATED -- implement `options` instead.
        """
        pass
    add_options = addOptions
    add_options.deprecated = True

    def addDeprecated(self, test):
        """Called when a deprecated test is seen. DO NOT return a value
        unless you want to stop other plugins from seeing the deprecated
        test.

        .. Note:: DEPRECATED -- check error class in addError instead

        :Parameters:
          test : `nose.case.Test`
            the test case 
        """
        pass
    addDeprecated.deprecated = True

    def addError(self, test, err):
        """Called when a test raises an uncaught exception. DO NOT return a
        value unless you want to stop other plugins from seeing that the
        test has raised an error.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
          capt : string
            Captured output, if any
            
            .. Note:: DEPRECATED: this parameter will not be passed
        """
        pass
    addError.changed = True

    def addFailure(self, test, err):
        """Called when a test fails. DO NOT return a value unless you
        want to stop other plugins from seeing that the test has failed.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
          capt : string
            Captured output, if any.

            .. Note:: DEPRECATED: this parameter will not be passed
          tb_info : string
            Introspected traceback info, if any
           
            .. Note:: DEPRECATED: this parameter will not be passed
        """
        pass
    addFailure.changed = True

    def addSkip(self, test):
        """Called when a test is skipped. DO NOT return a value unless
        you want to stop other plugins from seeing the skipped test.

        .. Note:: DEPRECATED -- check error class in addError instead

        :Parameters:
          test : `nose.case.Test`
            the test case
        """
        pass
    addSkip.deprecated = True

    def addSuccess(self, test, capt):
        """Called when a test passes. DO NOT return a value unless you
        want to stop other plugins from seeing the passing test.

        :Parameters:
          test : `nose.case.Test`
            the test case
          capt : string
            Captured output, if any.

            .. Note:: DEPRECATED: this parameter will not be passed            
        """
        pass
    addSuccess.changed = True

    def afterContext(self):
        """Called after a context (generally a module) has been
        lazy-loaded, imported, setup, had its tests loaded and
        executed, and torn down.
        """
        pass
    afterContext._new = True

    def afterDirectory(self, path):
        """Called after all tests have been loaded from directory at path
        and run.

        :Parameters:
          path : string
            the directory that has finished processing
        """
        pass
    afterDirectory._new = True

    def afterImport(self, filename, module):
        """Called after module is imported from filename. afterImport
        is called even if the import failed.

        :Parameters:
          filename : string
            The file that was loaded
          module : string
            The name of the module
        """
        pass
    afterImport._new = True        

    def afterTest(self, test):
        """Called after the test has been run and the result recorded
        (after stopTest).

        :Parameters:
          test :  `nose.case.Test`
            the test case
        """
        pass
    afterTest._new = True

    def beforeContext(self):
        """Called before a context (generally a module) is
        examined. Since the context is not yet loaded, plugins don't
        get to know what the context is; so any context operations
        should use a stack that is pushed in `beforeContext` and popped
        in `afterContext` to ensure they operate symmetrically.

        `beforeContext` and `afterContext` are mainly
        useful for tracking and restoring global state around possible
        changes from within a context, whatever the context may be. If
        you need to operate on contexts themselves, see `startContext`
        and `stopContext`, which are passed the context in question, but
        are called after it has been loaded (imported in the module
        case).
        """
        pass
    beforeContext._new = True

    def beforeDirectory(self, path):
        """Called before tests are loaded from directory at path.

        :Parameters:
          path : string
            the directory that is about to be processed
        """
        pass
    beforeDirectory._new = True

    def beforeImport(self, filename, module):
        """Called before module is imported from filename.

        :Parameters:
          filename : string
            The file that will be loaded
          module : string
            The name of the module found in file
        """
    beforeImport._new = True
    
    def beforeTest(self, test):
        """Called before the test is run (before startTest).
        
        :Parameters:
          test : `nose.case.Test`
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
        """Called after all report output, including output from all
        plugins, has been sent to the stream. Use this to print final
        test results or perform final cleanup. Return None to allow
        other plugins to continue printing, any other value to stop
        them.
        """
        pass

    def describeTest(self, test):
        """Return a test description. Called by
        `nose.case.Test.shortDescription`.

        :Parameters:
          test : `nose.case.Test`
            the test case
        """
        pass
    describeTest._new = True

    def formatError(self, test, err):
        """Called in result.addError, before plugin.addError. If you
        want to replace or modify the error tuple, return a new error
        tuple.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
        """
        pass
    formatError._new = True
    formatError.chainable = True

    def formatFailure(self, test, err):
        """Called in result.addFailure, before plugin.addFailure. If you
        want to replace or modify the error tuple, return a new error
        tuple.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
        """
        pass
    formatFailure._new = True
    formatFailure.chainable = True

    def handleError(self, test, err):
        """Called on addError. To handle the error yourself and prevent normal
        error processing, return a true value.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
        """
        pass
    handleError._new = True

    def handleFailure(self, test, err):
        """Called on addFailure. To handle the failure yourself and
        prevent normal failure processing, return a true value.

        :Parameters:
          test : `nose.case.Test`
            the test case
          err : 3-tuple
            sys.exc_info() tuple
        """
        pass
    handleFailure._new = True

    def loadTestsFromDir(self, path):
        """Return iterable of tests from a directory. May be a
        generator.  Each item returned must be a runnable
        unittest.TestCase (or subclass) instance or suite instance.
        Return None if your plugin cannot collect any tests from
        directory.

        :Parameters:
          path : string
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

        :Parameters:
          module : python module 
            The module object
        """
        pass
    loadTestsFromModule.generative = True
    
    def loadTestsFromName(self, name, module=None, importPath=None):
        """Return tests in this file or module. Return None if you are not able
        to load any tests, or an iterable if you are. May be a
        generator.

        :Parameters:
          name : string
            The test name. May be a file or module name plus a test
            callable. Use split_test_name to split into parts. Or it might
            be some crazy name of your own devising, in which case, do
            whatever you want.
          module : python module
            Module from which the name is to be loaded
          importPath :
            Path from which file (must be a python module) was found
            
            .. Note:: DEPRECATED: this argument will NOT be passed.
        """
        pass
    loadTestsFromName.generative = True

    def loadTestsFromNames(self, names, module=None):
        """Return a tuple of (tests loaded, remaining names). Return
        None if you are not able to load any tests. Multiple plugins
        may implement loadTestsFromNames; the remaining name list from
        each will be passed to the next as input.

        :Parameters:
          names : iterable
            List of test names.
          module : python module
            Module from which the names are to be loaded
        """
        pass
    loadTestsFromNames._new = True
    loadTestsFromNames.chainable = True

    def loadTestsFromFile(self, filename):
        """Return tests in this file. Return None if you are not
        interested in loading any tests, or an iterable if you are and
        can load some. May be a generator. *If you are interested in
        loading tests from the file and encounter no errors, but find
        no tests, yield False or return [False].*

        .. Note:: This method replaces loadTestsFromPath from the 0.9
                  API.
        
        :Parameters:
           filename : string
             The full path to the file or directory.
        """
        pass
    loadTestsFromFile.generative = True
    loadTestsFromFile._new = True

    def loadTestsFromPath(self, path):
        """
        .. Note:: DEPRECATED -- use loadTestsFromFile instead
        """
        pass
    loadTestsFromPath.deprecated = True
    
    def loadTestsFromTestCase(self, cls):
        """Return tests in this test case class. Return None if you are
        not able to load any tests, or an iterable if you are. May be a
        generator.

        :Parameters:
          cls : class
            The test case class. Must be subclass of unittest.TestCase.
        """
        pass
    loadTestsFromTestCase.generative = True

    def loadTestsFromTestClass(self, cls):
        """Return tests in this test class. Class will *not* be a
        unittest.TestCase subclass. Return None if you are not able to
        load any tests, an iterable if you are. May be a generator.

        :Parameters:
          cls : class
            The test class. Must NOT be subclass of unittest.TestCase.
        """
        pass
    loadTestsFromTestClass._new = True
    loadTestsFromTestClass.generative = True

    def makeTest(self, obj, parent):
        """Given an object and its parent, return a test case. Must be
        a unittest.TestCase or TestSuite (or subclass) instance. This
        is called before default test loading to allow plugins to load
        an alternate test case or cases for an object. May be a generator.

        :Parameters:
          obj : any object
            The object to be made into a test
          parent : class, module or other object
            The parent of obj (eg, for a method, the class)
         """
        pass
    makeTest._new = True
    makeTest.generative = True

    def options(self, parser, env=os.environ):
        """Called to allow plugin to register command line
        options with the parser.

        Do *not* return a value from this method unless you want to stop
        all other plugins from setting their options.
        """
        pass
    options._new = True

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

        :Parameters:
          test : `nose.case.Test`
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

        :Parameters:
           test : `nose.case.Test`
             the test case
        """
        pass
    prepareTestCase._new = True
    
    def prepareTestLoader(self, loader):
        """Called before tests are loaded. To replace the test loader,
        return a test loader. To allow other plugins to process the
        test loader, return None. Only one plugin may replace the test
        loader. Only valid when using nose.TestProgram.

        :Parameters:
           loader : `nose.loader.TestLoader` or other loader instance
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
        the result (for instance, if you want to handle some
        exceptions in a unique way). Only one plugin may replace the
        result, but many may monkeypatch it. If you want to
        monkeypatch and stop other plugins from doing so, monkeypatch
        and return the patched result.

        :Parameters:
           result : `nose.result.TextTestResult` or other result instance
             the test result
        """
        pass
    prepareTestResult._new = True

    def prepareTestRunner(self, runner):
        """Called before tests are run. To replace the test runner,
        return a test runner. To allow other plugins to process the
        test runner, return None. Only valid when using nose.TesrProgram.

        :Parameters:
           runner : `nose.core.TextTestRunner` or other runner instance
             the test runner
        """
        pass
    prepareTestRunner._new = True
        
    def report(self, stream):
        """Called after all error output has been printed. Print your
        plugin's report to the provided stream. Return None to allow
        other plugins to print reports, any other value to stop them.

        :Parameters:
           stream : file-like object
             stream object; send your output here
        """
        pass

    def setOutputStream(self, stream):
        """Called before test output begins. To direct test output to a
        new stream, return a stream object, which must implement a
        `write(msg)` method. If you only want to note the stream, not
        capture or redirect it, then return None.

        :Parameters:
           stream : file-like object
             the original output stream
        """

    def startContext(self, context):
        """Called before context setup and the running of tests in the
        context. Note that tests have already been *loaded* from the
        context before this call.

        :Parameters:
           context : module, class or other object
             the context about to be setup. May be a module or class, or any
             other object that contains tests.
        """
        pass
    startContext._new = True
    
    def startTest(self, test):
        """Called before each test is run. DO NOT return a value unless
        you want to stop other plugins from seeing the test start.

        :Parameters:
           test : `nose.case.Test`
             the test case
        """
        pass

    def stopContext(self, context):
        """Called after the tests in a context have run and the
        context has been torn down.

        :Parameters:
           context : module, class or other object
             the context that has just been torn down.
        """
        pass
    stopContext._new = True
    
    def stopTest(self, test):
        """Called after each test is run. DO NOT return a value unless
        you want to stop other plugins from seeing that the test has stopped.

        :Parameters:
          test : `nose.case.Test`
            the test case
        """
        pass

    def testName(self, test):
        """Return a short test name. Called by `nose.case.Test.__str__`.

        :Parameters:
           test : `nose.case.Test`
             the test case
        """
        pass
    testName._new = True

    def wantClass(self, cls):
        """Return true if you want the main test selector to collect
        tests from this class, false if you don't, and None if you don't
        care.

        :Parameters:
           cls : class
             The class being examined by the selector
        """
        pass
    
    def wantDirectory(self, dirname):
        """Return true if you want test collection to descend into this
        directory, false if you do not, and None if you don't care.

        :Parameters:
           dirname : string
             Full path to directory being examined by the selector
        """
        pass
    
    def wantFile(self, file):
        """Return true if you want to collect tests from this file,
        false if you do not and None if you don't care.

        Change from 0.9: The optional package parameter is no longer passed.

        :Parameters:
          file : string
            Full path to file being examined by the selector
        """
        pass
    
    def wantFunction(self, function):
        """Return true to collect this function as a test, false to
        prevent it from being collected, and None if you don't care.

        :Parameters:
          function : function
            The function object being examined by the selector
        """
        pass
    
    def wantMethod(self, method):
        """Return true to collect this method as a test, false to
        prevent it from being collected, and None if you don't care.

        :Parameters:
          method : unbound method
            The method object being examined by the selector
        """    
        pass
    
    def wantModule(self, module):
        """Return true if you want to collection to descend into this
        module, false to prevent the collector from descending into the
        module, and None if you don't care.

        :Parameters:
          module : python module
            The module object being examined by the selecto
        """
        pass
    
    def wantModuleTests(self, module):
        """
        .. Note:: DEPRECATED -- this method will not be called, it has
                  been folded in to wantModule.
        """
        pass
    wantModuleTests.deprecated = True
    
