import logging
import os
import re
import sys
import unittest
from nose.config import Config
from nose.plugins import call_plugins
from nose.util import absfile, file_like, split_test_name, src, test_address

log = logging.getLogger(__name__)

class Selector(object):
    """Core test selector. Examines test candidates and determines whether,
    given the specified configuration, the test candidate should be selected
    as a test.
    """
    def __init__(self, conf):
        self.conf = conf
        self.configure(conf)

    def classInTests(self, cls, tests=None):
        if tests is None:
            return True
        return filter(None,
                      [ t.matches_class(cls) for t in tests])

    def configure(self, conf):
        self.exclude = conf.exclude
        self.ignoreFiles = conf.ignoreFiles
        self.include = conf.include
        self.plugins = conf.plugins
        self.match = conf.testMatch

    def fileInTests(self, file, tests=None):
        if tests is None:
            return True
        else:
            return filter(None,
                          [ t.matches_file(file) for t in tests ])
    
    def funcInTests(self, func, tests=None):
        if tests is None:
            return True
        return filter(None,
                      [ t.matches_function(func) for t in tests ])
        
    def matches(self, name):
        """Does the name match my requirements?

        To match, a name must match conf.testMatch OR conf.include
        and it must not match conf.exclude
        """
        return ((self.match.search(name)
                 or (self.include and
                     filter(None,
                            [inc.search(name) for inc in self.include])))
                and ((not self.exclude)
                     or not filter(None,
                                   [exc.search(name) for exc in self.exclude])
                 ))

    def methodInTests(self, method, tests=None):
        """Determine if a method is listed in the requested tests. To
        be consideed a match, the method's class must be in the class
        part of the test address, and the function part of the test
        address must match the method name or be None.
        """
        if tests is None:
            return True
        return filter(None,
                      [ t.matches_method(method) for t in tests ])

    def moduleInTests(self, module, tests=None, either=False):
        """Return a function that can tell whether a module is in this
        batch of tests.

        FIXME: it would be good to memoize this
        """        
        if tests is None:
            return True
        return filter(None,
                      [ t.matches_module(module, either) for t in tests ])
    
    def wantClass(self, cls, tests=None):
        """Is the class a wanted test class?

        A class must be a unittest.TestCase subclass, or match test name
        requirements.

        If self.tests is defined, the class must match something in
        self.tests: 
        """
        log.debug("Load tests from class %s?", cls)
        
        wanted = (not cls.__name__.startswith('_')
                  and (issubclass(cls, unittest.TestCase)
                       or self.match.search(cls.__name__)))
        log.debug("%s is wanted? %s", cls, wanted)
        plug_wants = call_plugins(self.plugins, 'wantClass', cls)        
        if plug_wants is not None:
            log.debug("Plugin setting selection of %s to %s", cls, plug_wants)
            wanted = plug_wants
        return wanted and self.classInTests(cls, tests)

    def wantDirectory(self, dirname, tests=None):
        """Is the directory a wanted test directory?

        All package directories match, so long as they do not match exclude. 
        All other directories must match test requirements.
        """
        log.debug("Want directory %s (%s)?", dirname, tests)

        init = os.path.join(dirname, '__init__.py')
        tail = os.path.basename(dirname)   
        if os.path.exists(init):
            wanted = (not self.exclude
                      or not filter(None,
                                    [exc.search(tail) for exc in self.exclude]
                                    ))
        else:
            wanted = (self.matches(tail)
                      or (self.conf.srcDirs
                          and tail in self.conf.srcDirs))
        plug_wants = call_plugins(self.plugins, 'wantDirectory',
                                  dirname)
        if plug_wants is not None:
            wanted = plug_wants
        in_tests = self.fileInTests(dirname, tests)
        log.debug("wantDirectory %s wanted %s, in_tests %s",
                  dirname, wanted, in_tests)
        return wanted and in_tests
    
    def wantFile(self, file, package=None, tests=None):
        """Is the file a wanted test file?

        If self.tests is defined, the file must match the file part of a test
        address in self.tests.

        The default implementation ignores the package setting, but it is
        passed in case plugins need to distinguish package from non-package
        files.
        """

        # never, ever load files that match anything in ignore
        # (.* _* and *setup*.py by default)
        base = os.path.basename(file)
        ignore_matches = [ ignore_this for ignore_this in self.ignoreFiles
                           if ignore_this.search(base) ]
        if ignore_matches:
            log.debug('%s matches ignoreFiles pattern; skipped',
                      base) 
            return False
        if not self.conf.includeExe and os.access(file, os.X_OK):
            log.info('%s is executable; skipped', file)
            return False
        in_tests = self.fileInTests(file, tests)
        if not in_tests:
            return False
        dummy, ext = os.path.splitext(base)
        pysrc = ext == '.py'

        wanted = pysrc and self.matches(base) 
        plug_wants = call_plugins(self.plugins, 'wantFile',
                                  file, package)
        if plug_wants is not None:
            wanted = plug_wants
        result = wanted or (pysrc and tests and in_tests)
        log.debug("wantFile %s wanted %s pysrc %s in_tests %s", file,
                  wanted, pysrc, in_tests)
        return result

    def wantFunction(self, function, tests=None):
        """Is the function a test function?

        If conf.function_only is defined, the function name must match
        function_only. Otherwise, the function name must match test
        requirements.
        """
        try:
            funcname = function.__name__
        except AttributeError:
            # not a function
            return False
        in_tests = self.funcInTests(function, tests)
        if not in_tests:
            return False    
        wanted = not funcname.startswith('_') and self.matches(funcname)
        plug_wants = call_plugins(self.plugins, 'wantFunction', function)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted

    def wantMethod(self, method, tests=None):
        """Is the method a test method?
                
        If conf.function_only is defined, the qualified method name
        (class.method) must match function_only. Otherwise, the base method
        name must match test requirements.
        """
        try:
            method_name = method.__name__
        except AttributeError:
            # not a method
            return False
        if method_name.startswith('_'):
            # never collect 'private' methods
            return False
        in_tests = self.methodInTests(method, tests)
        if not in_tests:
            return False        
        wanted = self.matches(method_name)
        plug_wants = call_plugins(self.plugins, 'wantMethod', method)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted
    
    def wantModule(self, module, tests=None):
        """Is the module a test module?

        The tail of the module name must match test requirements.

        If a module is wanted, it means that the module should be
        imported and examined. It does not mean that tests will be
        collected from the module; tests are only collected from
        modules where wantModuleTests() is true.
        """
        in_tests = self.moduleInTests(module, tests, either=True)
        if not in_tests:
            return False        
        wanted = self.matches(module.__name__.split('.')[-1])
        plug_wants = call_plugins(self.plugins, 'wantModule', module)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted or (tests and in_tests)

    def wantModuleTests(self, module, tests=None):
        """Collect tests from this module?

        The tail of the module name must match test requirements.

        If the modules tests are wanted, they will be collected by the
        standard test collector. If your plugin wants to collect tests
        from a module in some other way, it MUST NOT return true for
        wantModuleTests; that would not allow the plugin to collect
        tests, but instead cause the standard collector to collect tests.
        """
        in_tests = self.moduleInTests(module, tests)
        if not in_tests:
            return False
        
        # unittest compat: always load from __main__
        wanted = (self.matches(module.__name__.split('.')[-1])
                  or module.__name__ == '__main__')
        plug_wants = call_plugins(self.plugins, 'wantModuleTests',
                                  module)
        if plug_wants is not None:
            wanted = plug_wants        
        return wanted or (tests and in_tests)
        
defaultSelector = Selector        


class TestAddress(object):
    """A test address represents a user's request to run a particular
    test. The user may specify a filename or module (or neither),
    and/or a callable (a class, function, or method). The naming
    format for test addresses is:

    filename_or_module:callable

    Filenames that are not absolute will be made absolute relative to
    the working dir.

    The filename or module part will be considered a module name if it
    doesn't look like a file, that is, if it doesn't exist on the file
    system and it doesn't contain any directory separators and it
    doesn't end in .py.

    Callables may be a class name, function name, method name, or
    class.method specification.
    """
    def __init__(self, name, working_dir=None):
        if working_dir is None:
            working_dir = os.getcwd()
        self.name = name
        self.working_dir = working_dir
        self.filename, self.module, self.call = split_test_name(name)
        if self.filename is not None:
            self.filename = src(self.filename)
            if not os.path.isabs(self.filename):
                self.filename = os.path.abspath(os.path.join(working_dir,
                                                             self.filename))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: (%s, %s, %s)" % (self.name, self.filename,
                                     self.module, self.call)

    def matches_class(self, cls):
        """Does the class match my call part?
        """
        if self.call is None:
            return True
        try:
            clsn, dummy = self.call.split('.')
        except (ValueError, AttributeError):
            # self.call is not dotted, like: foo or Foo
            clsn, dummy = self.call, None
        return cls.__name__ == clsn
        
    def matches_file(self, filename):
        """Does the filename match my file part?
        """
        log.debug("matches_file? %s == %s", filename, self.filename)
        fn = self.filename
        if fn is None:
            return self.matches_file_as_module(filename)
        if fn.endswith('__init__.py'):
            dn = os.path.dn(fn)
        elif os.path.isdir(fn):
            dn = fn
        else:
            dn = None
        if os.path.isdir(filename):
            dirname = filename
        else:
            dirname = None
        # filename might be a directory and fn a file in that directory
        # if so the directory has to match for us to continue on?
        return (fn == filename
                or (dn is not None
                    and (filename.startswith(dn)
                         and len(filename) > len(dn)
                         and filename[len(dn)] == os.path.sep)
                    or (filename == dn))
                or (dirname is not None
                    and (dirname == fn
                         or (fn.startswith(dirname)
                             and len(fn) > len(dirname)
                             and fn[len(dirname)] == os.path.sep))))

    def matches_file_as_module(self, filename):
        """Match filename vs our module part. Convert our module into
        a path fragment, and return True if the filename contains that
        path fragment. This method should only be called when self.filename
        is None.
        """
        log.debug("Match file %s vs module %s", filename, self.module)
        mn = self.module
        if mn is None:
            # No filename or modname part; so we match any module, because
            # the only part we have defined is the call, which could be
            # in any module
            return True

        filename = src(filename)
        base, ext = os.path.splitext(filename)
        if ext and ext != '.py':
            # not a python source file: can't be a module
            log.debug("%s is not a python source file (%s)", filename, ext)
            return False

        # Turn the module name into a path and compare against
        # the filename, with the file extension and working_dir removed
        sep = os.path.sep
        mpath = os.path.sep.join(mn.split('.'))
        base = base[len(self.working_dir):]
        log.debug("Match file %s (from module %s) vs %s", mpath, mn, base)
        mod_match_re = re.compile(r'(^|%s)%s(%s|$)' % (sep, mpath, sep))
        if mod_match_re.search(base):
            # the file is likely to be a subpackage of my module
            log.debug('%s is a subpackage of %s', filename, mn)
            return True
        # Now see if my module might be a subpackage of the file
        rev_match_re = re.compile(r'%s(%s|$)' % (base, sep))
        if rev_match_re.match(sep + mpath):
            log.debug('%s is a subpackage of %s', mn, filename)
            return True
        return False        

    def matches_function(self, function):
        """Does the function match my call part?
        """
        if self.call is None:
            return True
        funcname = getattr(function, 'compat_func_name', function.__name__)
        log.debug("Match function name: %s == %s", funcname, self.call)
        return funcname == self.call
    
    def matches_method(self, method):
        """Does the method match my call part?
        """
        if self.call is None:
            return True
        mcls = method.im_class.__name__
        mname = getattr(method, 'compat_func_name', method.__name__)
        log.debug("Match method %s.%s == %s", mcls, mname, self.call)
        try:
            cls, func = self.call.split('.')
        except (ValueError, AttributeError):
            cls, func = self.call, None
        return mcls == cls and (mname == func or func is None)
    
    def matches_module(self, module, either=False):
        """Either = either my module can be a child of module or
        module can be a child of my module. Without either, the
        match is valid only if module is a child of my module.
        """
        log.debug("Match module %s == %s?", module.__name__, self.module)
        if self.module is None:
            if self.filename is None:
                # This test only has a callable part, so it could
                # match a callable in any module
                return True
            return self.matches_module_as_file(module)
        mname = module.__name__
        result = (subpackage_of(mname, self.module) or
                  (either and subpackage_of(self.module, mname)))
        log.debug("Module %s match %s (either: %s) result %s",
                  module.__name__, self.module, either, result)
        return result

    def matches_module_as_file(self, module):
        """Does this module match my filename property? The module name is
        adjusted if it has been loaded from a .pyc or .pyo file, with the
        extension replaced by .py.
        """
        mod_file = src(module.__file__)
        log.debug('Trying to matching module file %s as file', mod_file)
        return self.matches_file(mod_file)


# Helpers
def match_all(*arg, **kw):
    return True


def subpackage_of(modname, package):
    """Is module modname a subpackage of package?"""
    # quick negative case
    log.debug('subpackage_of(%s,%s)', modname, package)
    if not modname.startswith(package):
        log.debug('not %s startswith %s' , modname, package)
        return False
    if len(package) > len(modname):
        log.debug('package name longer than mod name')
        return False
    mod_parts = modname.split('.')
    pkg_parts = package.split('.')
    try:
        for p in pkg_parts:            
            pp = mod_parts.pop(0)
            log.debug('check part %s vs part %s', p, pp)
            if p != pp:
                return False
    except IndexError:
        log.debug('package %s more parts than modname %s', package, modname)
        return False
    return True

    
def test_addr(names, working_dir=None):
    if names is None:
        return None
    return [ TestAddress(name, working_dir) for name in names ]
