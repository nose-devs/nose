import logging
import os
import sys
import unittest
from nose.config import Config
from nose.plugins import call_plugins
from nose.util import absfile, file_like, split_test_name, test_address

log = logging.getLogger(__name__)

class Selector(object):
    """Core test selector. Examines test candidates and determines whether,
    given the specified configuration, the test candidate should be selected
    as a test.
    """
    def __init__(self, conf):
        self.conf = conf
        self.configure(conf)
    
    def anytest(self, func):
        """Check func against all tests. Funcs should return None if they
        don't apply, False if they apply but don't match, True if they apply
        and match. 

        Example: a func that wants tests based on what file they are in should
        return None for a test address that doesn't contain a file part. It
        should return true if a test address contains a file part that matches
        the comparison file, and False if a test address contains a file part
        that does not match the comparison file.
        """
        if not self.tests:
            return True
        
        log.debug('tests to check: %s', self.tests)
        matches = [ func(*test_tuple) for test_tuple in
                    map(split_test_name, self.tests) ]
        log.debug('anytest matches: %s', matches)
        res = filter(lambda x: x is not False, matches)
        log.debug('anytest result: %s', res)
        return res

    def classInTests(self, cls):
        def match(filename, modname, funcname, cls=cls):
            if funcname is None:
                return None
            try:
                clsn, dummy = funcname.split('.')
            except (ValueError, AttributeError):
                clsn, dummy = funcname, None
            return cls.__name__ == clsn
        return self.anytest(match)

    def configure(self, conf):
        self.exclude = conf.exclude
        self.ignoreFiles = conf.ignoreFiles
        self.include = conf.include
        self.plugins = conf.plugins
        self.match = conf.testMatch        
        self.tests = conf.tests
                      
    def fileInTests(self, file):
        orig = file
        if not os.path.isabs(file):
            file = absfile(file, self.conf.working_dir)
            log.debug("abs file %s is %s", orig, file)
        if file is None:
            log.debug("File %s does not exist" % orig)
            if self.tests:
                return False
            return True
        log.debug('Check file in tests')
        def match(filename, modname, funcname, file=file):
            return self.filematch(filename, modname, funcname, file)
        return self.anytest(match)

    def filematch(self, filename, modname, funcname, file):
        log.debug("Filematch (%s, %s, %s, %s)",
                  filename, modname, funcname, file)
        if filename is None:
            if modname is None:
                return None
            # be liberal... could this file possibly be this module?
            # return None if the module name, converted to a file
            # path, matches any part of the full filename
            mpath = os.path.sep.join(modname.split('.'))
            log.debug("Is module path %s in file %s?", mpath, file)
            if mpath in file:
                return None
            else:
                return False                    
        if not os.path.isabs(filename):
            filename = absfile(filename, self.conf.working_dir)
            log.debug("Abs match file: %s", filename)
            
        # A file is a match if it is an exact match, or if
        # the filename to match against is a directory (or package init file)
        # and the file appears to be under that directory. Files that
        # don't exist can't match.
        if filename is None:
            return False
        
        if filename.endswith('__init__.py'):
            dirname = os.path.dirname(filename)
        elif os.path.isdir(filename):
            dirname = filename
        else:
            dirname = None

        log.debug("Files are same: %s", filename == file)
        log.debug("Dirname: %s", dirname)
        if dirname is not None:
            log.debug("File startswith dirname: %s", file.startswith(dirname))
            try:
                log.debug("File has sep at end of dirname: %s == %s",
                          file[len(dirname)], os.path.sep)
            except IndexError:
                log.debug("File is not within dir")
        
        return filename == file \
               or (dirname is not None
                   and file.startswith(dirname)
                   and file[len(dirname)] == os.path.sep)

    def funcInTests(self, func):
        def match(filename, modname, funcname, func=func):
            if funcname is None:
                return None
            return func.__name__ == funcname
        return self.anytest(match)
        
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
    
    def methodInTests(self, method):
        """Determine if a method is listed in the requested tests. To
        be consideed a match, the method's class must be in the class
        part of the test address, and the function part of the test
        address must match the method name or be None.
        """
        def match(filename, modname, funcname, method=method):
            if funcname is None:
                return None
            mcls = method.im_class.__name__
            mname = method.__name__
            try:
                cls, func = funcname.split('.')
            except (ValueError, AttributeError):
                cls, func = funcname, None
            return mcls == cls and (mname == func or func is None)
        return self.anytest(match)

    def moduleInTests(self, module, either=False):
        def match(filename, modname, funcname, module=module, either=either):
            log.debug("Checking module %s in test %s:%s (either: %s)",
                      module.__name__, modname, funcname, either)
            if modname is None:
                if filename is None:                
                    return None
                mod_file = module.__file__
                if mod_file.endswith('.pyc') or mod_file.endswith('.pyo'):
                    mod_file = mod_file[:-3] + 'py'
                log.debug("Checking module file %s against filename %s",
                          mod_file, filename)
                return self.filematch(filename, modname, funcname,
                                      file=mod_file)
            mname = module.__name__
            result = (subpackage_of(mname, modname) or
                      (either and subpackage_of(modname, mname)))
            log.debug("Module %s match %s (either: %s) result %s",
                      module.__name__, modname, either, result)
            return result
        res = self.anytest(match)
        log.debug("Module %s in tests result: %s", module,res)
        return res
    
    def wantClass(self, cls):
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
        return wanted and self.classInTests(cls)

    def wantDirectory(self, dirname):
        """Is the directory a wanted test directory?

        All package directories match, so long as they do not match exclude. All
        other directories must match test requirements.
        """
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
        # FIXME in tests?
        return wanted
    
    def wantFile(self, file, package=None):
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
        in_tests = self.fileInTests(file)
        if not in_tests:
            return False
        dummy, ext = os.path.splitext(base)
        pysrc = ext == '.py'

        wanted = pysrc and self.matches(base) 
        plug_wants = call_plugins(self.plugins, 'wantFile',
                                  file, package)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted or (pysrc and self.tests and in_tests)

    def wantFunction(self, function):
        """Is the function a test function?

        If conf.function_only is defined, the function name must match
        function_only. Otherwise, the function name must match test
        requirements.
        """
        try:
            if hasattr(function, 'compat_func_name'):
                funcname = function.compat_func_name
            else:
                funcname = function.__name__
        except AttributeError:
            # not a function
            return False
        in_tests = self.funcInTests(function)
        if not in_tests:
            return False    
        wanted = not funcname.startswith('_') and self.matches(funcname)
        plug_wants = call_plugins(self.plugins, 'wantFunction', function)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted

    def wantMethod(self, method):
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
        in_tests = self.methodInTests(method)
        if not in_tests:
            return False        
        wanted = self.matches(method_name)
        plug_wants = call_plugins(self.plugins, 'wantMethod', method)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted
    
    def wantModule(self, module):
        """Is the module a test module?

        The tail of the module name must match test requirements.

        If a module is wanted, it means that the module should be loaded,
        and its setup/teardown fixtures run -- if any. It does not mean that
        tests will be collected from the module; tests are only collected from
        modules where wantModuleTests() is true.
        """
        in_tests = self.moduleInTests(module, either=True)
        if not in_tests:
            return False        
        wanted = self.matches(module.__name__.split('.')[-1])
        plug_wants = call_plugins(self.plugins, 'wantModule', module)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted or (self.tests and in_tests)

    def wantModuleTests(self, module):
        """Collect tests from this module?

        The tail of the module name must match test requirements.

        If the modules tests are wanted, they will be collected by the
        standard test collector. If your plugin wants to collect tests
        from a module in some other way, it MUST NOT return true for
        wantModuleTests; that would not allow the plugin to collect
        tests, but instead cause the standard collector to collect tests.
        """
        in_tests = self.moduleInTests(module)
        if not in_tests:
            return False
        
        # unittest compat: always load from __main__
        wanted = (self.matches(module.__name__.split('.')[-1])
                  or module.__name__ == '__main__')
        plug_wants = call_plugins(self.plugins, 'wantModuleTests',
                                  module)
        if plug_wants is not None:
            wanted = plug_wants        
        return wanted or (self.tests and in_tests)
        
defaultSelector = Selector        

# Helpers

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
    
