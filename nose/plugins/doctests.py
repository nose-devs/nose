"""Use the Doctest plugin with --with-doctest or the NOSE_WITH_DOCTEST
environment variable to enable collection and execution of doctests. doctest_
tests are usually included in the tested package, not grouped into packages or
modules of their own. For this reason, nose will try to detect and run doctest
tests only in the non-test packages it discovers in the working
directory. Doctests may also be placed into files other than python modules,
in which case they can be collected and executed by using the
--doctest-extension switch or NOSE_DOCTEST_EXTENSION environment variable to
indicate which file extension(s) to load.

doctest tests are run like any other test, with the exception that output
capture does not work, because doctest does its own output capture in the
course of running a test.

.. _doctest: http://docs.python.org/lib/module-doctest.html
"""
import doctest
import logging
import os
import sys
from nose.plugins.base import Plugin
from nose.util import anyp, test_address, resolve_name, tolist

log = logging.getLogger(__name__)

# FIXME can't return a naked doctest suite -- the parent will be wrong (it
# will be set to doctest, not the module the doctests were loaded from) so
# we need to wrap the returned suite in a test or something that has the
# proper parent set

class Doctest(Plugin):
    """
    Activate doctest plugin to find and run doctests in non-test modules.
    """
    extension = None
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option('--doctest-tests', action='store_true',
                          dest='doctest_tests',
                          default=env.get('NOSE_DOCTEST_TESTS'),
                          help="Also look for doctests in test modules "
                          "[NOSE_DOCTEST_TESTS]")
        try:
            # 2.4 or better supports loading tests from non-modules
            doctest.DocFileSuite
            parser.add_option('--doctest-extension', action="append",
                              dest="doctestExtension",
                              help="Also look for doctests in files with "
                              "this extension [NOSE_DOCTEST_EXTENSION]")
            # Set the default as a list, if given in env; otherwise
            # an additional value set on the command line will cause
            # an error.
            env_setting = env.get('NOSE_DOCTEST_EXTENSION')
            if env_setting is not None:
                parser.set_defaults(doctestExtension=tolist(env_setting))
        except AttributeError:
            pass

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.doctest_tests = options.doctest_tests
        try:
            self.extension = tolist(options.doctestExtension)
        except AttributeError:
            # 2.3, no other-file option
            self.extension = None
        self.finder = doctest.DocTestFinder()

    def loadTestsFromModule(self, module):
        if not self.matches(module.__name__):
            log.debug("Doctest doesn't want module %s", module)
            return
        try:
            doctests = doctest.DocTestSuite(module)
        except ValueError:
            log.debug("No doctests in %s", module)
            return
        else:
            return self.makeTests(doctests)
            
    def loadTestsFromFile(self, filename):
        if self.extension and anyp(filename.endswith, self.extension):
            try:
                return self.makeTests(
                    doctest.DocFileSuite(filename, module_relative=False))
            except AttributeError:
                raise Exception("Doctests in files other than .py "
                                "(python source) not supported in this "
                                "version of doctest")
        else:
            return

    def makeTest(self, obj, parent):
        """Look for doctests in the given object, which will be a
        function, method or class.
        """
        try:
            # FIXME really find the module, don't assume parent
            # is a module
            doctests = self.finder.find(obj, module=parent)
        except ValueError:
            yield Failure(*sys.exc_info())
            return
        if doctests:
            for test in doctests:
                if len(test.examples) == 0:
                    continue
                yield TestProxy(doctest.DocTestCase(test), obj)
            

    def makeTests(self, doctests):
        if hasattr(doctests, '__iter__'):
            doctest_suite = doctests
        else:
            doctest_suite = doctests._tests
        return map(TestProxy, doctest_suite)            
    
    def matches(self, name):
        """Doctest wants only non-test modules in general.
        """
        # FIXME this seems wrong -- nothing is ever going to
        # fail this test, since we're given a module NAME not FILE
        if name == '__init__.py':
            return False
        # FIXME don't think we need include/exclude checks here?
        return ((self.doctest_tests or not self.conf.testMatch.search(name)
                 or (self.conf.include 
                     and filter(None,
                                [inc.search(name)
                                 for inc in self.conf.include])))
                and (not self.conf.exclude 
                     or not filter(None,
                                   [exc.search(name)
                                    for exc in self.conf.exclude])))
    
    def wantFile(self, file):
        # always want .py files
        if file.endswith('.py'):
            return True
        # also want files that match my extension
        if (self.extension
            and anyp(file.endswith, self.extension)
            and (self.conf.exclude is None
                 or not self.conf.exclude.search(file))):
            return True
        return None
        

class TestProxy(object):
    """Proxy for DocTestCase: provides an address() method that
    returns the correct address for the doctest case. Otherwise
    acts as a proxy to the test case. To provide hints for address(),
    an obj may also be passed -- this will be used as the test object
    for purposes of determining the test address, if it is provided.
    """
    def __init__(self, case, obj=None):
        self.__dict__['case'] = case
        self.__dict__['_tp_obj'] = obj

    def address(self):
        if self.__dict__['_tp_obj'] is not None:
            return test_address(self.__dict__['_tp_obj'])
        return test_address(resolve_name(self.__dict__['case']._dt_test.name))

    def __getattr__(self, attr):
        return getattr(self.__dict__['case'], attr)

    def __setattr__(self, attr, val):
        setattr(self.__dict__['case'], attr, val)

    def __call__(self, *arg, **kw):
        return self.__dict__['case'](*arg, **kw)

    # Annoyingly, doctests loaded via find(obj) omit the module name
    # so we need to override id, __str__ and shortDescription
    # bonus: this will squash a 2.3 vs 2.4 incompatiblity

    def __str__(self):
        return str(self.case)

    def __repr__(self):
        return repr(self.case)
