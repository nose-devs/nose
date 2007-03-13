import os
import re
import textwrap
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
    enabled = False
    enableOpt = None
    name = None

    def __init__(self):
        if self.name is None:
            self.name = self.__class__.__name__.lower()
        if self.enableOpt is None:
            self.enableOpt = "enable_plugin_%s" % self.name
            
    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin.

        The base plugin class adds --with-$name by default, used to enable the
        plugin. 
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
    below. Please note that they `must not` subclass PluginInterface;
    PluginInterface is a only description of the plugin API.

    When plugins are called, the first plugin that implements a method
    and returns a non-None value wins, and plugin processing ends. The
    only exceptions to are `loadTestsFromModule`, `loadTestsFromName`,
    and `loadTestsFromPath`, which allow multiple plugins to load and
    return tests.

    In general, plugin methods correspond directly to the methods of
    nose.selector.Selector, nose.loader.TestLoader and
    nose.result.TextTestResult are called by those methods when they are
    called. In some cases, the plugin hook doesn't neatly match the
    method in which it is called; for those, the documentation for the
    hook will tell you where in the test process it is called.

    Plugin hooks fall into two broad categories: selecting and loading
    tests, and watching and reporting on test results.
    
    Selecting and loading tests
    ===========================

    To alter test selection behavior, implement any necessary want*
    methods as outlined below. Keep in mind, though, that when your
    plugin returns True from a want* method, you will send the requested
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
        """
        pass

    # FIXME beforeTest, afterTest

    def addDeprecated(self, test, err):
        """Called when a deprecated test is seen. DO NOT return a value
        unless you want to stop other plugins from seeing the deprecated
        test.

        Parameters:
         * test:
           the test case 
        """
        pass

    def addError(self, test, err, capt):
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
        """
        pass

    def addFailure(self, test, err, capt, tb_info):
        """Called when a test fails. DO NOT return a value unless you
        want to stop other plugins from seeing that the test has failed.

        Parameters:
         * test:
           the test case
         * err:
           sys.exc_info() tuple
         * capt:
           Captured output, if any
         * tb_info:
           Introspected traceback info, if any
        """
        pass

    def addSkip(self, test, err):
        """Called when a test is skipped. DO NOT return a value unless
        you want to stop other plugins from seeing the skipped test.

        Parameters:
         * test:
           the test case
        """
        pass        

    def addSuccess(self, test, capt):
        """Called when a test passes. DO NOT return a value unless you
        want to stop other plugins from seeing the passing test.

        Parameters:
         * test:
           the test case
         * capt:
           Captured output, if any
        """
        pass        
            
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

    # FIXME loadTestsFromClass, loadTestsFromDir
    
    def loadTestsFromModule(self, module):
        """Return iterable of tests in a module. May be a
        generator. Each item returned must be a runnable
        unittest.TestCase subclass. Return None if your plugin cannot
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
           Module in which the file is found
         * importPath:
           Path from which file (must be a python module) was found
           DEPRECATED: this argument will NOT be passed.
        """
        pass
    loadTestsFromName.generative = True

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

        Parameters:
         * cls:
           The test case class
        """
        pass
    loadTestsFromTestCase.generative = True
    
    def prepareTest(self, test):
        """Called before the test is run by the test runner. Please note
        the article *the* in the previous sentence: prepareTest is
        called *only once*, and is passed the test case or test suite
        that the test runner will execute. It is *not* called for each
        individual test case. If you return a non-None value,
        that return value will be run as the test. Use this hook to wrap
        or decorate the test with another function.

        Parameters:
         * test:
           the test case
        """
        pass

    # FIXME prepareTestCase
    
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
        write(msg) method. If you only want to note the stream, not
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
    
    def wantFile(self, file, package=None):
        """Return true if you want to collect tests from this file,
        false if you do not and None if you don't care.

        Parameters:
         * file:
           Full path to file
         * package:
           Package in which file is found, if any
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
    
