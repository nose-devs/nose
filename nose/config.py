import logging
import os
import re
import sys
import ConfigParser
from optparse import OptionParser
from nose.util import absdir, tolist
from warnings import warn

log = logging.getLogger(__name__)

# not allowed in config files
option_blacklist = ['help', 'verbose']

config_files = [
    # Linux users will prefer this
    "~/.noserc",
    # Windows users will prefer this
    "~/nose.cfg"
    ]


class Config(object):
    """nose configuration.

    Instances of Config are used throughout nose to configure
    behavior, including plugin lists. Here are the default values for
    all config keys::

      self.env = env = kw.pop('env', os.environ)
      self.args = ()
      self.testMatch = re.compile(r'(?:^|[\b_\.%s-])[Tt]est' % os.sep)
      self.addPaths = not env.get('NOSE_NOPATH', False)
      self.configSection = 'nosetests'
      self.debug = env.get('NOSE_DEBUG')
      self.debugLog = env.get('NOSE_DEBUG_LOG')
      self.exclude = None
      self.getTestCaseNamesCompat = False
      self.includeExe = env.get('NOSE_INCLUDE_EXE',
                                sys.platform == 'win32')
      self.ignoreFiles = (re.compile(r'^\.'),
                          re.compile(r'^_'),
                          re.compile(r'^setup\.py$')
                          )
      self.include = None
      self.loggingConfig = None
      self.logStream = sys.stderr
      self.options = ()
      self.parser = None
      self.plugins = NoPlugins()
      self.srcDirs = ('lib', 'src')
      self.runOnInit = True
      self.stopOnError = env.get('NOSE_STOP', False)
      self.stream = sys.stderr
      self.testNames = ()
      self.verbosity = int(env.get('NOSE_VERBOSE', 1))
      self.where = ()
      self.workingDir = None   
    """

    def __init__(self, **kw):
        self.env = env = kw.pop('env', os.environ)
        self.args = ()
        self.testMatchPat = env.get('NOSE_TESTMATCH',
                                    r'(?:^|[\b_\.%s-])[Tt]est' % os.sep)
        self.testMatch = re.compile(self.testMatchPat)
        self.addPaths = not env.get('NOSE_NOPATH', False)
        self.configSection = 'nosetests'
        self.debug = env.get('NOSE_DEBUG')
        self.debugLog = env.get('NOSE_DEBUG_LOG')
        self.exclude = None
        self.getTestCaseNamesCompat = False
        self.includeExe = env.get('NOSE_INCLUDE_EXE',
                                  sys.platform == 'win32')
        self.ignoreFiles = (re.compile(r'^\.'),
                            re.compile(r'^_'),
                            re.compile(r'^setup\.py$')
                            )
        self.include = None
        self.loggingConfig = None
        self.logStream = sys.stderr
        self.options = ()
        self.parser = None
        self.plugins = NoPlugins()
        self.srcDirs = ('lib', 'src')
        self.runOnInit = True
        self.stopOnError = env.get('NOSE_STOP', False)
        self.stream = sys.stderr
        self.testNames = ()
        self.verbosity = int(env.get('NOSE_VERBOSE', 1))
        self.where = ()
        self.workingDir = None
        
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
        env = self.env
        if argv is None:
            argv = sys.argv
        if hasattr(self, 'files'):
            argv = self.loadConfig(self.files, argv)
        parser = self.getParser(doc)        
        options, args = parser.parse_args(argv)
        # If -c --config has been specified on command line,
        # load those config files to create a new argv set and reparse
        if options.files:
            argv = self.loadConfig(options.files, argv)
            options, args = parser.parse_args(argv)       
        try:
            self.options, self.testNames = options, args[1:]
        except IndexError:
            self.options = options

        if options.testNames is not None:
            self.testNames.extend(tolist(options.testNames))

        # `where` is an append action, so it can't have a default value 
        # in the parser, or that default will always be in the list
        if not options.where:
            options.where = env.get('NOSE_WHERE', None)

        # include and exclude also
        if not options.include:
            options.include = env.get('NOSE_INCLUDE', [])
        if not options.exclude:
            options.exclude = env.get('NOSE_EXCLUDE', [])

        self.addPaths = options.addPaths
        self.stopOnError = options.stopOnError
        self.verbosity = options.verbosity
        self.includeExe = options.includeExe
        self.debug = options.debug
        self.debugLog = options.debugLog
        self.loggingConfig = options.loggingConfig
        self.configureLogging()

        if options.testMatch:
            self.testMatch = re.compile(options.testMatch)
        
        if options.where is not None:
            self.configureWhere(options.where)

        if options.include:
            self.include = map(re.compile, tolist(options.include))
            log.info("Including tests matching %s", options.include)

        if options.exclude:
            self.exclude = map(re.compile, tolist(options.exclude))
            log.info("Excluding tests matching %s", options.exclude)

        # When listing plugins we don't want to run them
        if not options.showPlugins:
            self.plugins.configure(options, self)
            self.plugins.begin()

    def configureLogging(self):
        """Configure logging for nose, or optionally other packages. Any logger
        name may be set with the debug option, and that logger will be set to
        debug level and be assigned the same handler as the nose loggers, unless
        it already has a handler.
        """
        if self.loggingConfig:
            logging.fileConfig(self.loggingConfig)
            return
        
        format = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
        if self.debugLog:
            handler = logging.FileHandler(self.debugLog)
        else:
            handler = logging.StreamHandler(self.logStream)
        handler.setFormatter(format)

        logger = logging.getLogger('nose')
        logger.propagate = 0

        # only add our default handler if there isn't already one there
        # this avoids annoying duplicate log messages.
        if not logger.handlers:
            logger.addHandler(handler)

        # default level    
        lvl = logging.WARNING
        if self.verbosity >= 5:
            lvl = 0
        elif self.verbosity >= 4:
            lvl = logging.DEBUG
        elif self.verbosity >= 3:
            lvl = logging.INFO
        logger.setLevel(lvl)

        # individual overrides
        if self.debug:
            # no blanks
            debug_loggers = [ name for name in self.debug.split(',')
                              if name ]
            for logger_name in debug_loggers:
                l = logging.getLogger(logger_name)
                l.setLevel(logging.DEBUG)
                if not l.handlers and not logger_name.startswith('nose'):
                    l.addHandler(handler)

    def configureWhere(self, where):
        """Configure the working director for the test run.
        """
        from nose.importer import add_path
        where = tolist(where)
        warned = False
        for path in where:
            if not self.workingDir:
                abs_path = absdir(path)
                if abs_path is None:
                    raise ValueError("Working directory %s not found, or "
                                     "not a directory" % path)
                log.info("Set working dir to %s", abs_path)
                self.workingDir = abs_path
                if self.addPaths and \
                       os.path.exists(os.path.join(abs_path, '__init__.py')):
                    log.info("Working directory %s is a package; "
                             "adding to sys.path" % abs_path)
                    add_path(abs_path)
                continue
            if not warned:
                warn("Use of multiple -w arguments is deprecated and "
                     "support may be removed in a future release. You can "
                     "get the same behavior by passing directories without "
                     "the -w argument on the command line, or by using the "
                     "--tests argument in a configuration file.",
                     DeprecationWarning)
            self.testNames.append(path)

    def default(self):
        """Reset all config values to defaults.
        """
        self.__dict__.update(self._default)

    def getParser(self, doc=None):
        """Get the command line option parser.
        """
        if self.parser:
            return self.parser
        env = self.env
        parser = OptionParser(doc)
        parser.add_option(
            "-V","--version", action="store_true",
            dest="version", default=False,
            help="Output nose version and exit")
        parser.add_option(
            "-p", "--plugins", action="store_true",
            dest="showPlugins", default=False,
            help="Output list of available plugins and exit. Combine with "
            "higher verbosity for greater detail")
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
            "-q", "--quiet", action="store_const", const=0, dest="verbosity")
        parser.add_option(
            "-c", "--config", action="append", dest="files",
            help="Load configuration from config file(s). May be specified "
            "multiple times; in that case, all config files will be "
            "loaded and combined")
        parser.add_option(
            "-w", "--where", action="append", dest="where",
            help="Look for tests in this directory. "
            "May be specified multiple times. The first directory passed "
            "will be used as the working directory, in place of the current "
            "working directory, which is the default. Others will be added "
            "to the list of tests to execute. [NOSE_WHERE]"
            )
        parser.add_option("-m", "--match", "--testmatch", action="store",
                          dest="testMatch",
                          help="Use this regular expression to "
                          "find tests [NOSE_TESTMATCH]",
                          default=self.testMatchPat)
        parser.add_option(
            "--tests", action="store", dest="testNames", default=None,
            help="Run these tests (comma-separated list). This argument is "
            "useful mainly from configuration files; on the command line, "
            "just pass the tests to run as additional arguments with no "
            "switch.")
        parser.add_option(
            "-l", "--debug", action="store",
            dest="debug", default=self.debug,
            help="Activate debug logging for one or more systems. "
            "Available debug loggers: nose, nose.importer, "
            "nose.inspector, nose.plugins, nose.result and "
            "nose.selector. Separate multiple names with a comma.")
        parser.add_option(
            "--debug-log", dest="debugLog", action="store",
            default=self.debugLog,
            help="Log debug messages to this file "
            "(default: sys.stderr)")
        parser.add_option(
            "--logging-config", "--log-config",
            dest="loggingConfig", action="store",
            default=self.loggingConfig,
            help="Load logging config from this file -- bypasses all other"
            " logging config settings.")
        parser.add_option(
            "-e", "--exclude", action="append", dest="exclude",
            help="Don't run tests that match regular "
            "expression [NOSE_EXCLUDE]")
        parser.add_option(
            "-i", "--include", action="append", dest="include",
            help="Also run tests that match regular "
            "expression [NOSE_INCLUDE]")
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

        self.plugins.loadPlugins()
        self.pluginOpts(parser)

        self.parser = parser
        return parser

    def loadConfig(self, file, argv):
        """Load config from file (may be filename or file-like object) and
        push the config into argv.
        """
        cfg = ConfigParser.RawConfigParser()
        try:
            try:
                cfg.readfp(file)
            except AttributeError:
                # Filename not an fp
                cfg.read(file)
        except ConfigParser.Error, e:
            warn("Error reading config file %s: %s" % (file, e),
                 RuntimeWarning)
            return argv
        if self.configSection not in cfg.sections():
            return argv
        file_argv = []
        for optname in cfg.options(self.configSection):
            if optname in option_blacklist:
                continue
            value = cfg.get(self.configSection, optname)
            file_argv.extend(self.cfgToArg(optname, value))
        # Copy the given args and insert args loaded from file
        # between the program name (first arg) and the rest
        combined = argv[:]
        combined[1:1] = file_argv
        return combined

    def cfgToArg(self, optname, value, tr=None):
        if tr is not None:
            optname = tr(optname)
        argv = []
        if flag(value):
            if _bool(value):
                argv.append('--' + optname)
        else:
            argv.append('--' + optname)
            argv.append(value)
        return argv

    def pluginOpts(self, parser):
        self.plugins.addOptions(parser, self.env)

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


def user_config_files():
    """Return path to any existing user config files
    """
    return filter(os.path.exists,
                  map(os.path.expanduser, config_files))


def all_config_files():
    """Return path to any existing user config files, plus any setup.cfg
    in the current working directory.
    """
    user = user_config_files()
    if os.path.exists('setup.cfg'):
        return user + ['setup.cfg']
    return user


# used when parsing config files
def flag(val):
    """Does the value look like an on/off flag?"""
    if len(val) > 5:
        return False
    return val.upper() in ('1', '0', 'F', 'T', 'TRUE', 'FALSE', 'ON', 'OFF')


def _bool(val):
    return val.upper() in ('1', 'T', 'TRUE', 'ON')
