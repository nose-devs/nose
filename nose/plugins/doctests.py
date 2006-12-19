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
from nose.plugins.base import Plugin
from nose.util import anyp, tolist

log = logging.getLogger(__name__)

#
# Doctest and coverage don't get along, so we need to create
# a monkeypatch that will replace the part of doctest that
# interferes with coverage reports.
#
# The monkeypatch is based on this zope patch:
# http://svn.zope.org/Zope3/trunk/src/zope/testing/doctest.py?rev=28679&r1=28703&r2=28705
#
_orp = doctest._OutputRedirectingPdb

class NoseOutputRedirectingPdb(_orp):
    def __init__(self, out):
        self.__debugger_used = False
        _orp.__init__(self, out)

    def set_trace(self):
        self.__debugger_used = True
        _orp.set_trace(self)

    def set_continue(self):
        # Calling set_continue unconditionally would break unit test coverage
        # reporting, as Bdb.set_continue calls sys.settrace(None).
        if self.__debugger_used:
            _orp.set_continue(self)
doctest._OutputRedirectingPdb = NoseOutputRedirectingPdb


class Doctest(Plugin):
    """
    Activate doctest plugin to find and run doctests in non-test modules.
    """
    extension = None
    
    def add_options(self, parser, env=os.environ):
        Plugin.add_options(self, parser, env)
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
            # < 2.4 doctest (and unittest) suites don't have iterators
            log.debug("Doctests found in %s", module)
            if hasattr(doctests, '__iter__'):
                doctest_suite = doctests
            else:
                doctest_suite = doctests._tests
            for test in doctest_suite:
                yield test
            
    def loadTestsFromPath(self, filename, package=None, importPath=None):
        if self.extension and anyp(filename.endswith, self.extension):
            try:
                return doctest.DocFileSuite(filename, module_relative=False)
            except AttributeError:
                raise Exception("Doctests in files other than .py "
                                "(python source) not supported in this "
                                "version of doctest")
        else:
            # Don't return None, users may iterate over result
            return []
    
    def matches(self, name):
        """Doctest wants only non-test modules in general.
        """
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
    
    def wantFile(self, file, package=None):
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
        
