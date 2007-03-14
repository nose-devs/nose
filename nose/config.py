import os
import re
import sys


class Config(object):
    """nose configuration. For internal use only.
    """

    def __init__(self, **kw):
        self.testMatch = re.compile(r'(?:^|[\b_\.%s-])[Tt]est' % os.sep)
        self.addPaths = True
        self.capture = True
        self.detailedErrors = False
        self.debugErrors = False
        self.debugFailures = False
        self.exclude = None
        self.includeExe = sys.platform=='win32'
        self.ignoreFiles = [ re.compile(r'^\.'),
                             re.compile(r'^_'),
                             re.compile(r'^setup\.py$')
                             ]
        self.include = None
        self.plugins = NoPlugins()
        self.resultProxy = None
        self.srcDirs = ['lib', 'src']
        self.stopOnError = False
        self.tests = []
        self.verbosity = 1
        self._where = None
        self._working_dir = None
        self.update(kw)
        self._orig = self.__dict__.copy()

    # FIXME maybe kill all this and instantiate a new config for each
    # working dir
    def get_where(self):
        return self._where

    def set_where(self, val):
        self._where = val
        self._working_dir = None

    def get_working_dir(self):
        val = self._working_dir
        if val is None:
            if isinstance(self.where, list) or isinstance(self.where, tuple):
                val = self._working_dir = self.where[0]
            else:
                val = self._working_dir = self.where
        return val

    def set_working_dir(self, val):
        self._working_dir = val
        
    def __str__(self):
        # FIXME -- in alpha order
        return repr(self.__dict__)

    def reset(self):
        self.__dict__.update(self._orig)

    def todict(self):
        return self.__dict__.copy()
        
    def update(self, d):
        self.__dict__.update(d)

    # properties
    where = property(get_where, set_where, None,
                     "The list of directories where tests will be discovered")
    working_dir = property(get_working_dir, set_working_dir, None,
                           "The current working directory (the root "
                           "directory of the current test run).")


class NoPlugins(object):

    def __getattr__(self, call):
        return self

    def __call__(self, *arg, **kw):
        return
