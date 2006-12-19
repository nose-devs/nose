import os
import re
from imp import load_source
from nose.selector import Selector, TestAddress, test_addr
from nose.config import Config
from nose.importer import _import
from nose.util import split_test_name

#import logging
#logging.basicConfig()
#logging.getLogger('').setLevel(0)

conf = Config()
selector = Selector(conf)


def ispackage(dirname):
    return os.path.exists(os.path.join(dirname, '__init__.py'))


def ispackageinit(module):
    filename = module.__file__
    base, ext = os.path.splitext(os.path.basename(filename))
    return base == '__init__' and ext.startswith('.py')


def module_name(filename, package=None):
    base, junk = os.path.splitext(filename)
    if package is None:
        return base
    return "%s.%s" % (package, base)


class ModuleSuite:
    def __init__(self, name, path, loader, working_dir, tests):
        # FIXME name -> modulename
        #       path -> filename
        #       document tests vs _tests
        self.name = name
        self.path = path
        self.module = None
        self.loader = loader
        self.working_dir = working_dir
        self.tests = tests
        self._collected = False
        self._tests = []

    def __nonzero__(self):
        self.collectTests()
        return bool(self._tests)

    def __len__(self):
        self.collectTests()
        return len(self._tests)

    def __iter__(self):
        self.collectTests()
        return iter(self._tests)

    def __str__(self):
        return "ModuleSuite(%s, %s)" % (self.name, self.path)

    def addTest(self, test):
        # depth-first?
        if test:
            self._tests.append(test)

    def collectTests(self):
        # print "Collect Tests %s" % self
        if self._collected or self._tests:
            return
        self._collected = True
        self._tests = []
        if self.module is None:
            # We know the exact source of each module so why not?
            # We still need to add the module's parent dir (up to the top
            # if it's a package) to sys.path first, though
            self.module = load_source(self.name, self.path)
        for test in self.loader.loadTestsFromModule(self.module, self.tests):
            self.addTest(test)
        
    def run(self, result):
        # startTest
        self.collectTests()
        if not self:
            return
        # FIXME this needs to be a real run() with exc handling
        self.setUp()
        for test in self._tests:
            test(result)
        self.tearDown()
        # stopTest()
        
    def setUp(self):
        print "SETUP %s" % self

    def tearDown(self):
        print "TEARDOWN %s" % self
        
        
class TestLoader:

    # FIXME move collectTests to DirectorySuite
    
    def collectTests(self, working_dir, names=None):
        if not os.path.isabs(working_dir):
            working_dir = os.path.join(os.getcwd(), working_dir)
        tests = test_addr(names, working_dir)
        return self.findTests(working_dir, tests=tests)
    
    def findTests(self, working_dir, tests=None, package=None):
        for dirpath, dirnames, filenames in os.walk(working_dir):

            # FIXME first sort dirnames into test-last order
            
            to_remove = set()
            packages = []
            for dirname in dirnames:

                # FIXME if it looks like a lib dir, continue in
                # FIXME and add it to sys.path
                
                remove = True
                ldir = os.path.join(dirpath, dirname)
                if selector.wantDirectory(ldir, tests=tests):
                    if ispackage(ldir):
                        remove = True
                        # we'll yield a ModuleSuite later
                        packages.append((dirname,
                                         os.path.join(ldir, '__init__.py')))
                    else:
                        remove = False
                        # print "Continue into %s" % ldir
                if remove:
                    to_remove.add(dirname)
            for dirname in to_remove:
                dirnames.remove(dirname)

            # Process files after dirs so that any lib dirs will
            # already be in sys.path before we start importing files
                
            for filename in filenames:
                if filename.endswith('.pyc') or filename.endswith('.pyo'):
                    continue
                lname = os.path.join(dirpath, filename)
                if selector.wantFile(lname, package=package, tests=tests):
                    # print "**", lname
                    yield ModuleSuite(
                        name=module_name(filename, package=package),
                        path=lname, loader=self,
                        working_dir=working_dir,
                        tests=tests)
                    # FIXME yield a ModuleSuite if it's a python module
                    # FIXME yield a FileSuite if it's not
            # yield ModuleSuites for all packages
            for name, path in packages:
                yield ModuleSuite(
                    name=module_name(name, package=package),
                    path=path, loader=self,
                    working_dir=working_dir,
                    tests=tests)
            # At this point we're diving into directories that aren't packages
            # so if we think we are in a package, we have to forget the
            # package name, lest modules in the directory think their names
            # are package.foo when they are really just foo
            package = None
                
    def loadTestsFromModule(self, module, tests=None):
        """Construct a TestSuite containing all of the tests in
        the module, including tests in the package if it is a package
        """
        # print "loadTestsFromModule %s" % module
        if ispackageinit(module):
            path = os.path.dirname(module.__file__)
            for test in self.findTests(path, tests, package=module.__name__):
                # FIXME
                print "  ", test
        return []

if __name__ == '__main__':
    import sys
    l = TestLoader()
    for test in l.collectTests('unit_tests/support', sys.argv[1:]):
        print test
        test.run('whatever')
    #mods = sys.modules.keys()[:]
    #mods.sort()
    #print mods
    
# note these testable possibilities
# need a test for each of these
#'test.py' => 'support/test.py'
#'foo' => 'support/foo'
#'test-dir/test.py' => 'support/test-dir/test.py'
#'test-dir' => 'support/test-dir/test.py'
#'test-dir/' => 'support/test-dir/test.py'
#'test' => 'support/test.py'
#'foo.bar' => 'support/foo/bar'    
