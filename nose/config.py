import logging
import os
import re
import sys
from optparse import OptionParser
from nose.util import absdir, tolist

log = logging.getLogger(__name__)

class Config(object):
    """nose configuration.

    self.testMatch = re.compile(r'(?:^|[\b_\.%s-])[Tt]est' % os.sep)
    self.addPaths = True
    self.capture = True
    self.detailedErrors = False
    self.debugErrors = False
    self.debugFailures = False
    self.exclude = None
    self.exit = True
    self.includeExe = sys.platform=='win32'
    self.ignoreFiles = ( re.compile(r'^\.'),
                         re.compile(r'^_'),
                         re.compile(r'^setup\.py$')
                         )
    self.include = None
    self.plugins = NoPlugins()
    self.srcDirs = ('lib', 'src')
    self.runOnInit = True
    self.stopOnError = False
    self.stream = sys.stderr
    self.testNames = ()
    self.verbosity = 1
    self.where = ('.',)
    """

    def __init__(self, **kw):
        self.env = env = kw.pop('env', os.environ)
        self.args = ()
        self.testMatch = re.compile(r'(?:^|[\b_\.%s-])[Tt]est' % os.sep)
        self.addPaths = not env.get('NOSE_NOPATH', False)
        self.capture = not env.get('NOSE_NOCAPTURE', False)
        self.detailedErrors = env.get('NOSE_DETAILED_ERRORS', False)
        self.debug = env.get('NOSE_DEBUG')
        self.debugLog = env.get('NOSE_DEBUG_LOG')
        self.exclude = None
        self.exit = True
        self.includeExe = env.get('NOSE_INCLUDE_EXE',
                                  sys.platform == 'win32')
        self.ignoreFiles = (re.compile(r'^\.'),
                            re.compile(r'^_'),
                            re.compile(r'^setup\.py$')
                            )
        self.include = None
        self.options = ()
        self.plugins = NoPlugins()
        self.srcDirs = ('lib', 'src')
        self.runOnInit = True
        self.stopOnError = env.get('NOSE_STOP', False)
        self.stream = sys.stderr
        self.testNames = ()
        self.verbosity = int(env.get('NOSE_VERBOSE', 1))
        self.where = ()
        
        self._default = self.__dict__.copy()
        self.update(kw)
        self._orig = self.__dict__.copy()
        #        self._where = None
        #        self._working_dir = None

    def __repr__(self):
        d = self.__dict__
        keys = [ k for k in d.keys()
                 if not k.startswith('_') ]
        keys.sort()
        return "Config(%s)" % ', '.join([ '%s=%r' % (k, d[k])
                                          for k in keys ])
    __str__ = __repr__

    def configure(self, argv=None, doc=None):
        """Configure the nose running environment. Execute configure before
        collecting tests with nose.TestCollector to enable output capture and
        other features.
        """

        # get a parser
        # load plugins
        # let plugins set opts
        # parse argv
        # configure self and plugins
        # testNames = non-option args

        if argv is None:
            argv = sys.argv
        env = self.env
        
        self.getParser(doc)
        self.plugins.loadPlugins()
        self.pluginOpts()
        
        options, args = self.parser.parse_args(argv)
        try:
            self.options, self.testNames = options, args[1:]
        except IndexError:
            self.options = options

        # where is an append action, so it can't have a default value 
        # in the parser, or that default will always be in the list
        if not options.where:
            options.where = env.get('NOSE_WHERE', None)

        # include and exclude also
        if not options.include:
            options.include = env.get('NOSE_INCLUDE', [])
        if not options.exclude:
            options.exclude = env.get('NOSE_EXCLUDE', [])

        self.configureLogging(options)
        self.addPaths = options.addPaths
        self.capture = options.capture
        self.detailedErrors = options.detailedErrors
        self.debugErrors = options.debugErrors
        self.debugFailures = options.debugFailures
        self.stopOnError = options.stopOnError
        self.verbosity = options.verbosity
        self.includeExe = options.includeExe

        if options.where is not None:
            for path in tolist(options.where):
                log.debug('Adding %s as nose working directory', path)
                abs_path = absdir(path)
                if abs_path is None:
                    raise ValueError("Working directory %s not found, or "
                                     "not a directory" % path)
                self.testNames.append(abs_path)
                log.info("Looking for tests in %s", abs_path)
                if self.addPaths and \
                       os.path.exists(os.path.join(abs_path, '__init__.py')):
                    log.info("Working directory %s is a package; "
                             "adding to sys.path" % abs_path)
                    add_path(abs_path)

        if options.include:
            self.include = map(re.compile, tolist(options.include))
            log.info("Including tests matching %s", options.include)

        if options.exclude:
            self.exclude = map(re.compile, tolist(options.exclude))
            log.info("Excluding tests matching %s", options.exclude)

        self.plugins.configure(options, self)
        self.plugins.begin()

    def configureLogging(self, options):
        # FIXME
        # logging.basicConfig(level=logging.DEBUG)
        pass

    def default(self):
        self.__dict__.update(self._default)

    def getParser(self, doc=None):
        env = self.env
        parser = OptionParser(doc)
        parser.add_option(
            "-V","--version",action="store_true",
            dest="version",default=False,
            help="Output nose version and exit")
        parser.add_option(
            "-v", "--verbose",
            action="count", dest="verbosity",
            default=self.verbosity,
            help="Be more verbose. [NOSE_VERBOSE]")
        parser.add_option(
            "--verbosity", action="store", dest="verbosity",
            type="int", help="Set verbosity; --verbosity=2 is "
            "the same as -vv")
        parser.add_option(
            "-l", "--debug", action="store",
            dest="debug", default=self.debug,
            help="Activate debug logging for one or more systems. "
            "Available debug loggers: nose, nose.importer, "
            "nose.inspector, nose.plugins, nose.result and "
            "nose.selector. Separate multiple names with a comma.")
        parser.add_option(
            "--debug-log", dest="debug_log", action="store",
            default=self.debugLog,
            help="Log debug messages to this file "
            "(default: sys.stderr)")
        parser.add_option(
            "-q", "--quiet", action="store_const",
            const=0, dest="verbosity")
        parser.add_option(
            "-w", "--where", action="append", dest="where",
            help="DEPRECATED Look for tests in this directory. "
            "This option is deprecated; you can pass the directories "
            "without using -w for the same behavior. [NOSE_WHERE]"
            )
        parser.add_option(
            "-e", "--exclude", action="append", dest="exclude",
            help="Don't run tests that match regular "
            "expression [NOSE_EXCLUDE]")
        parser.add_option(
            "-i", "--include", action="append", dest="include",
            help="Also run tests that match regular "
            "expression [NOSE_INCLUDE]")
        parser.add_option(
            "-s", "--nocapture", action="store_false",
            default=self.capture, dest="capture",
            help="Don't capture stdout (any stdout output "
            "will be printed immediately) [NOSE_NOCAPTURE]")
        parser.add_option(
            "-d", "--detailed-errors", action="store_true",
            default=self.detailedErrors,
            dest="detailedErrors", help="Add detail to error"
            " output by attempting to evaluate failed"
            " asserts [NOSE_DETAILED_ERRORS]")
        parser.add_option(
            "-x", "--stop", action="store_true", dest="stopOnError",
            default=self.stopOnError,
            help="Stop running tests after the first error or failure")
        parser.add_option(
            "-P", "--no-path-adjustment", action="store_false",
            dest="addPaths",
            default=self.addPaths,
            help="Don't make any changes to sys.path when "
            "loading tests [NOSE_NOPATH]")
        parser.add_option(
            "--exe", action="store_true", dest="includeExe",
            default=self.includeExe,
            help="Look for tests in python modules that are "
            "executable. Normal behavior is to exclude executable "
            "modules, since they may not be import-safe "
            "[NOSE_INCLUDE_EXE]")
        parser.add_option(
            "--noexe", action="store_false", dest="includeExe",
            help="DO NOT look for tests in python modules that are "
            "executable. (The default on the windows platform is to "
            "do so.)")
        self.parser = parser
        return parser

    def pluginOpts(self):
        self.plugins.addOptions(self.parser, self.env)

    def reset(self):
        self.__dict__.update(self._orig)

    def todict(self):
        return self.__dict__.copy()
        
    def update(self, d):
        self.__dict__.update(d)


class NoPlugins(object):
    """Plugin 'manager' that includes no plugins and returns None
    for all calls
    """
    def __getattr__(self, call):
        return self

    def __call__(self, *arg, **kw):
        return



# deprecated
    # FIXME maybe kill all this and instantiate a new config for each
    # working dir
#     def get_where(self):
#         return self._where

#     def set_where(self, val):
#         self._where = val
#         self._working_dir = None

#     def get_working_dir(self):
#         val = self._working_dir
#         if val is None:
#             if isinstance(self.where, list) or isinstance(self.where, tuple):
#                 val = self._working_dir = self.where[0]
#             else:
#                 val = self._working_dir = self.where
#         return val

#     def set_working_dir(self, val):
#         self._working_dir = val
        

#     # properties
#     where = property(get_where, set_where, None,
#                      "The list of directories where tests will be discovered")
#     working_dir = property(get_working_dir, set_working_dir, None,
#                            "The current working directory (the root "
#                            "directory of the current test run).")
