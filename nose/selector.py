import logging
import os
import re
import sys
import unittest
from nose.config import Config
from nose.util import absfile, file_like, split_test_name, src, test_address, \
     getfilename, getpackage

log = logging.getLogger(__name__)

class Selector(object):
    """Core test selector. Examines test candidates and determines whether,
    given the specified configuration, the test candidate should be selected
    as a test.
    """
    def __init__(self, conf):
        self.conf = conf
        self.configure(conf)

    def configure(self, conf):
        self.exclude = conf.exclude
        self.ignoreFiles = conf.ignoreFiles
        self.include = conf.include
        self.plugins = conf.plugins
        self.match = conf.testMatch
        
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
    
    def wantClass(self, cls):
        """Is the class a wanted test class?

        A class must be a unittest.TestCase subclass, or match test name
        requirements. Classes that start with _ are always excluded.
        """
        declared = getattr(cls, '__test__', None)
        if declared is not None:
            wanted = declared
        else:
            wanted = (not cls.__name__.startswith('_')
                      and (issubclass(cls, unittest.TestCase)
                           or self.matches(cls.__name__)))
        
        plug_wants = self.plugins.wantClass(cls)        
        if plug_wants is not None:
            log.debug("Plugin setting selection of %s to %s", cls, plug_wants)
            wanted = plug_wants
        log.debug("wantClass %s? %s", cls, wanted)
        return wanted

    def wantDirectory(self, dirname):
        """Is the directory a wanted test directory?

        All package directories match, so long as they do not match exclude. 
        All other directories must match test requirements.
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
        plug_wants = self.plugins.wantDirectory(dirname)
        if plug_wants is not None:
            log.debug("Plugin setting selection of %s to %s",
                      dirname, plug_wants)
            wanted = plug_wants
        log.debug("wantDirectory %s? %s", dirname, wanted)
        return wanted
    
    def wantFile(self, file):
        """Is the file a wanted test file?

        The file must be a python source file and match testMatch or
        include, and not match exclude. Files that match ignore are *never*
        wanted, regardless of plugin, testMatch, include or exclude settings.
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
        dummy, ext = os.path.splitext(base)
        pysrc = ext == '.py'

        wanted = pysrc and self.matches(base) 
        plug_wants = self.plugins.wantFile(file)
        if plug_wants is not None:
            log.debug("plugin setting want %s to %s", file, plug_wants)
            wanted = plug_wants
        log.debug("wantFile %s? %s", file, wanted)
        return wanted

    def wantFunction(self, function):
        """Is the function a test function?
        """
        try:
            funcname = function.__name__
        except AttributeError:
            # not a function
            return False
        declared = getattr(function, '__test__', None)
        if declared is not None:
            wanted = declared
        else:
            wanted = not funcname.startswith('_') and self.matches(funcname)
        plug_wants = self.plugins.wantFunction(function)
        if plug_wants is not None:
            wanted = plug_wants
        log.debug("wantFunction %s? %s", function, wanted)
        return wanted

    def wantMethod(self, method):
        """Is the method a test method?
        """
        try:
            method_name = method.__name__
        except AttributeError:
            # not a method
            return False
        if method_name.startswith('_'):
            # never collect 'private' methods
            return False
        declared = getattr(method, '__test__', None)
        if declared is not None:
            wanted = declared
        else:
            wanted = self.matches(method_name)
        plug_wants = self.plugins.wantMethod(method)
        if plug_wants is not None:
            wanted = plug_wants
        log.debug("wantMethod %s? %s", method, wanted)
        return wanted
    
    def wantModule(self, module):
        """Is the module a test module?

        The tail of the module name must match test requirements. One exception:
        we always want __main__.
        """
        declared = getattr(module, '__test__', None)
        if declared is not None:
            wanted = declared
        else:
            wanted = self.matches(module.__name__.split('.')[-1]) \
                     or module.__name__ == '__main__'
        plug_wants = self.plugins.wantModule(module)
        if plug_wants is not None:
            wanted = plug_wants
        return wanted
        
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
    def __init__(self, name, workingDir=None):
        if workingDir is None:
            workingDir = os.getcwd()
        self.name = name
        self.workingDir = workingDir
        self.filename, self.module, self.call = split_test_name(name)
        log.debug('Test name %s resolved to file %s, module %s, call %s',
                  name, self.filename, self.module, self.call)
        if self.filename is None:
            if self.module is not None:
                self.filename = getfilename(self.module, self.workingDir)
        if self.filename:
            self.filename = src(self.filename)
            if not os.path.isabs(self.filename):
                self.filename = os.path.abspath(os.path.join(workingDir,
                                                             self.filename))
            if self.module is None:
                self.module = getpackage(self.filename)
        log.debug(
            'Final resolution of test name %s: file %s module %s call %s',
            name, self.filename, self.module, self.call)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: (%s, %s, %s)" % (self.name, self.filename,
                                     self.module, self.call)

#     def matches_class(self, cls):
#         """Does the class match my call part?
#         """
#         if self.call is None:
#             return True
#         try:
#             clsn, dummy = self.call.split('.')
#         except (ValueError, AttributeError):
#             # self.call is not dotted, like: foo or Foo
#             clsn, dummy = self.call, None
#         return cls.__name__ == clsn
        
#     def matches_file(self, filename):
#         """Does the filename match my file part?
#         """
#         log.debug("matches_file? %s == %s", filename, self.filename)
#         fn = self.filename
#         if fn is None:
#             return self.matches_file_as_module(filename)
#         if fn.endswith('__init__.py'):
#             dn = os.path.dn(fn)
#         elif os.path.isdir(fn):
#             dn = fn
#         else:
#             dn = None
#         if os.path.isdir(filename):
#             dirname = filename
#         else:
#             dirname = None
#         # filename might be a directory and fn a file in that directory
#         # if so the directory has to match for us to continue on?
#         return (fn == filename
#                 or (dn is not None
#                     and (filename.startswith(dn)
#                          and len(filename) > len(dn)
#                          and filename[len(dn)] == os.path.sep)
#                     or (filename == dn))
#                 or (dirname is not None
#                     and (dirname == fn
#                          or (fn.startswith(dirname)
#                              and len(fn) > len(dirname)
#                              and fn[len(dirname)] == os.path.sep))))

#     def matches_file_as_module(self, filename):
#         """Match filename vs our module part. Convert our module into
#         a path fragment, and return True if the filename contains that
#         path fragment. This method should only be called when self.filename
#         is None.
#         """
#         log.debug("Match file %s vs module %s", filename, self.module)
#         mn = self.module
#         if mn is None:
#             # No filename or modname part; so we match any module, because
#             # the only part we have defined is the call, which could be
#             # in any module
#             return True

#         filename = src(filename)
#         base, ext = os.path.splitext(filename)
#         if ext and ext != '.py':
#             # not a python source file: can't be a module
#             log.debug("%s is not a python source file (%s)", filename, ext)
#             return False

#         # Turn the module name into a path and compare against
#         # the filename, with the file extension and workingDir removed
#         sep = os.path.sep
#         mpath = os.path.sep.join(mn.split('.'))
#         base = base[len(self.workingDir):]
#         log.debug("Match file %s (from module %s) vs %s", mpath, mn, base)
#         mod_match_re = re.compile(r'(^|%s)%s(%s|$)' % (sep, mpath, sep))
#         if mod_match_re.search(base):
#             # the file is likely to be a subpackage of my module
#             log.debug('%s is a subpackage of %s', filename, mn)
#             return True
#         # Now see if my module might be a subpackage of the file
#         rev_match_re = re.compile(r'%s(%s|$)' % (base, sep))
#         if rev_match_re.match(sep + mpath):
#             log.debug('%s is a subpackage of %s', mn, filename)
#             return True
#         return False        

#     def matches_function(self, function):
#         """Does the function match my call part?
#         """
#         if self.call is None:
#             return True
#         funcname = getattr(function, 'compat_func_name', function.__name__)
#         log.debug("Match function name: %s == %s", funcname, self.call)
#         return funcname == self.call
    
#     def matches_method(self, method):
#         """Does the method match my call part?
#         """
#         if self.call is None:
#             return True
#         mcls = method.im_class.__name__
#         mname = getattr(method, 'compat_func_name', method.__name__)
#         log.debug("Match method %s.%s == %s", mcls, mname, self.call)
#         try:
#             cls, func = self.call.split('.')
#         except (ValueError, AttributeError):
#             cls, func = self.call, None
#         return mcls == cls and (mname == func or func is None)
    
#     def matches_module(self, module, either=False):
#         """Either = either my module can be a child of module or
#         module can be a child of my module. Without either, the
#         match is valid only if module is a child of my module.
#         """
#         log.debug("Match module %s == %s?", module.__name__, self.module)
#         if self.module is None:
#             if self.filename is None:
#                 # This test only has a callable part, so it could
#                 # match a callable in any module
#                 return True
#             return self.matches_module_as_file(module)
#         mname = module.__name__
#         result = (subpackage_of(mname, self.module) or
#                   (either and subpackage_of(self.module, mname)))
#         log.debug("Module %s match %s (either: %s) result %s",
#                   module.__name__, self.module, either, result)
#         return result

#     def matches_module_as_file(self, module):
#         """Does this module match my filename property? The module name is
#         adjusted if it has been loaded from a .pyc or .pyo file, with the
#         extension replaced by .py.
#         """
#         mod_file = src(module.__file__)
#         log.debug('Trying to matching module file %s as file', mod_file)
#         return self.matches_file(mod_file)


# # Helpers
# def match_all(*arg, **kw):
#     return True


# def subpackage_of(modname, package):
#     """Is module modname a subpackage of package?"""
#     # quick negative case
#     log.debug('subpackage_of(%s,%s)', modname, package)
#     if not modname.startswith(package):
#         log.debug('not %s startswith %s' , modname, package)
#         return False
#     if len(package) > len(modname):
#         log.debug('package name longer than mod name')
#         return False
#     mod_parts = modname.split('.')
#     pkg_parts = package.split('.')
#     try:
#         for p in pkg_parts:            
#             pp = mod_parts.pop(0)
#             log.debug('check part %s vs part %s', p, pp)
#             if p != pp:
#                 return False
#     except IndexError:
#         log.debug('package %s more parts than modname %s', package, modname)
#         return False
#     return True

    
# def test_addr(names, workingDir=None):
#     if names is None:
#         return None
#     return [ TestAddress(name, workingDir) for name in names ]
