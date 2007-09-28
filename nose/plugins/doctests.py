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

This module also includes a specialized version of nose.run() that
makes it easier to write doctests that test test runs.

.. _doctest: http://docs.python.org/lib/module-doctest.html
"""
from __future__ import generators

import logging
import os
from inspect import getmodule
from nose.plugins.base import Plugin
from nose.util import anyp, getpackage, test_address, resolve_name, tolist
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

log = logging.getLogger(__name__)

try:
    import doctest
    doctest.DocTestCase
    # system version of doctest is acceptable, but needs a monkeypatch
except (ImportError, AttributeError):
    # system version is too old
    import nose.ext.dtcompat as doctest


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
        # Calling set_continue unconditionally would break unit test 
        # coverage reporting, as Bdb.set_continue calls sys.settrace(None).
        if self.__debugger_used:
            _orp.set_continue(self)
doctest._OutputRedirectingPdb = NoseOutputRedirectingPdb    


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
                          help="Also look for doctests in test modules. "
                          "Note that classes, methods and functions should "
                          "have either doctests or non-doctest tests, "
                          "not both. [NOSE_DOCTEST_TESTS]")
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
        tests = self.finder.find(module)
        if not tests:
            return
        tests.sort()
        module_file = module.__file__
        if module_file[-4:] in ('.pyc', '.pyo'):
            module_file = module_file[:-1]
        for test in tests:
            if not test.examples:
                continue
            if not test.filename:
                test.filename = module_file
            yield DocTestCase(test)
            
    def loadTestsFromFile(self, filename):
        if self.extension and anyp(filename.endswith, self.extension):
            name = os.path.basename(filename)
            dh = open(filename)
            try:
                doc = dh.read()
            finally:
                dh.close()
            parser = doctest.DocTestParser()
            test = parser.get_doctest(
                doc, globs={'__file__': filename}, name=name,
                filename=filename, lineno=0)
            if test.examples:
                yield DocFileCase(test)
            else:
                yield False # no tests to load
            
    def makeTest(self, obj, parent):
        """Look for doctests in the given object, which will be a
        function, method or class.
        """
        doctests = self.finder.find(obj, module=getmodule(parent))
        if doctests:
            for test in doctests:
                if len(test.examples) == 0:
                    continue
                yield DocTestCase(test, obj=obj)            
    
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
            and (not self.conf.exclude
                 or not filter(None, 
                               [exc.search(file)
                                for exc in self.conf.exclude]))):
            return True
        return None
        

class DocTestCase(doctest.DocTestCase):
    """Proxy for DocTestCase: provides an address() method that
    returns the correct address for the doctest case. Otherwise
    acts as a proxy to the test case. To provide hints for address(),
    an obj may also be passed -- this will be used as the test object
    for purposes of determining the test address, if it is provided.
    """
    def __init__(self, test, optionflags=0, setUp=None, tearDown=None,
                 checker=None, obj=None):
        self._nose_obj = obj
        super(DocTestCase, self).__init__(
            test, optionflags=optionflags, setUp=None, tearDown=None,
            checker=None)
    
    def address(self):
        if self._nose_obj is not None:
            return test_address(self._nose_obj)
        return test_address(resolve_name(self._dt_test.name))
    
    # doctests loaded via find(obj) omit the module name
    # so we need to override id, __repr__ and shortDescription
    # bonus: this will squash a 2.3 vs 2.4 incompatiblity
    def id(self):
        name = self._dt_test.name
        filename = self._dt_test.filename
        if filename is not None:
            pk = getpackage(filename)
            if not name.startswith(pk):
                name = "%s.%s" % (pk, name)
        return name
    
    def __repr__(self):
        name = self.id()
        name = name.split('.')
        return "%s (%s)" % (name[-1], '.'.join(name[:-1]))
    __str__ = __repr__
                           
    def shortDescription(self):
        return 'Doctest: %s' % self.id()


class DocFileCase(doctest.DocFileCase):
    """Overrides to provide filename
    """
    def address(self):
        return (self._dt_test.filename, None, None)


def run(*arg, **kw):
    """DEPRECATED: moved to nose.plugins.plugintest.
    """
    import warnings
    warnings.warn("run() has been moved to nose.plugins.plugintest. Please "
                  "update your imports.", category=DeprecationWarning)
    from nose.plugins.plugintest import run
    run(*arg, **kw)
