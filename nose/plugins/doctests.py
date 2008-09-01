"""Use the Doctest plugin with --with-doctest or the NOSE_WITH_DOCTEST
environment variable to enable collection and execution of doctests. doctest_
tests are usually included in the tested package, not grouped into packages or
modules of their own. For this reason, nose will try to detect and run doctest
tests only in the non-test packages it discovers in the working
directory.

Doctests may also be placed into files other than python modules, in which
case they can be collected and executed by using the --doctest-extension
switch or NOSE_DOCTEST_EXTENSION environment variable to indicate which file
extension(s) to load.

When loading doctests from non-module files, you may specify how to find
modules that contains fixtures for the tests using the --doctest-fixtures
switch. The value of that switch will be appended to the base name of each
doctest file loaded to produce a module name. For instance, for a doctest file
"widgets.rst" with the switch ``--doctest_fixtures=_fixt``, fixtures will be
loaded from the module ``widgets_fixt.py`` if it exists.

A fixtures module may define any or all of the following functions:

* setup([module]) or setup_module([module])
   
  Called before any tests are run. You may raise SkipTest to skip all tests.
  
* teardown([module]) or teardown_module([module])

  Called after all tests are run, if setup/setup_module did not raise an
  unhandled exception.

* setup_test(test)

  Called before each test in the file. NOTE: the argument passed is a
  doctest.DocTest instance, *not* a unittest.TestCase.
  
* teardown_test(test)
 
  Called after each test in the file whose setup_test call did not raise an
  unhandled exception. NOTE: the argument passed is a doctest.DocTest
  instance, *not* a unittest.TestCase
  
Doctest tests are run like any other test, with the exception that output
capture does not work, because doctest does its own output capture in the
course of running a test.

.. _doctest: http://docs.python.org/lib/module-doctest.html
"""
from __future__ import generators

import logging
import os
import sys
import unittest
from inspect import getmodule
from nose.plugins.base import Plugin
from nose.suite import ContextSuite
from nose.util import anyp, getpackage, test_address, resolve_name, \
     src, tolist, isproperty
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import sys
import __builtin__

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
        _orp.set_trace(self, sys._getframe().f_back)

    def set_continue(self):
        # Calling set_continue unconditionally would break unit test 
        # coverage reporting, as Bdb.set_continue calls sys.settrace(None).
        if self.__debugger_used:
            _orp.set_continue(self)
doctest._OutputRedirectingPdb = NoseOutputRedirectingPdb    


class DoctestSuite(unittest.TestSuite):
    """
    Doctest suites are parallelizable at the module or file level only,
    since they may be attached to objects that are not individually
    addressable (like properties). This suite subclass is used when
    loading doctests from a module to ensure that behavior.

    This class is used only if the plugin is not fully prepared;
    in normal use, the loader's suiteClass is used.
    
    """
    can_split = False
    
    def __init__(self, tests=(), context=None, can_split=False):
        self.context = context
        self.can_split = can_split
        unittest.TestSuite.__init__(self, tests=tests)

    def address(self):
        return test_address(self.context)

    def __iter__(self):
        # 2.3 compat
        return iter(self._tests)

    def __str__(self):
        return str(self._tests)

        
class Doctest(Plugin):
    """
    Activate doctest plugin to find and run doctests in non-test modules.
    """
    extension = None
    suiteClass = DoctestSuite
    
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
        parser.add_option('--doctest-result-variable',
                          dest='doctest_result_var',
                          default=env.get('NOSE_DOCTEST_RESULT_VAR'),
                          help="Change the variable name set to the result of "
                          "the last interpreter command from the default '_'. "
                          "Can be used to avoid conflicts with the _() "
                          "function used for text translation. "
                          "[NOSE_DOCTEST_RESULT_VAR]")
        parser.add_option('--doctest-fixtures', action="store",
                          dest="doctestFixtures",
                          help="Find fixtures for a doctest file in module "
                          "with this name appended to the base name "
                          "of the doctest file")
        # Set the default as a list, if given in env; otherwise
        # an additional value set on the command line will cause
        # an error.
        env_setting = env.get('NOSE_DOCTEST_EXTENSION')
        if env_setting is not None:
            parser.set_defaults(doctestExtension=tolist(env_setting))

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.doctest_result_var = options.doctest_result_var
        self.doctest_tests = options.doctest_tests
        self.extension = tolist(options.doctestExtension)
        self.fixtures = options.doctestFixtures
        self.finder = doctest.DocTestFinder()

    def prepareTestLoader(self, loader):
        self.suiteClass = loader.suiteClass

    def loadTestsFromModule(self, module):
        log.debug("loading from %s", module)
        if not self.matches(module.__name__):
            log.debug("Doctest doesn't want module %s", module)
            return
        try:
            tests = self.finder.find(module)
        except AttributeError:
            log.exception("Attribute error loading from %s", module)
            # nose allows module.__test__ = False; doctest does not and throws
            # AttributeError
            return
        if not tests:
            log.debug("No tests found in %s", module)
            return
        tests.sort()
        module_file = src(module.__file__)
        # FIXME this breaks the id plugin somehow (tests probably don't
        # get wrapped in result proxy or something)
        cases = []
        for test in tests:
            if not test.examples:
                continue
            if not test.filename:
                test.filename = module_file            
            cases.append(DocTestCase(test, result_var=self.doctest_result_var))
        if cases:
            yield self.suiteClass(cases, context=module, can_split=False)
            
    def loadTestsFromFile(self, filename):
        if self.extension and anyp(filename.endswith, self.extension):
            name = os.path.basename(filename)
            dh = open(filename)
            try:
                doc = dh.read()
            finally:
                dh.close()

            fixture_context = None
            globs = {'__file__': filename}
            if self.fixtures:
                base, ext = os.path.splitext(name)
                dirname = os.path.dirname(filename)
                sys.path.append(dirname)
                fixt_mod = base + self.fixtures
                try:
                    fixture_context = __import__(
                        fixt_mod, globals(), locals(), ["nop"])
                except ImportError, e:
                    log.debug(
                        "Could not import %s: %s (%s)", fixt_mod, e, sys.path)
                log.debug("Fixture module %s resolved to %s",
                          fixt_mod, fixture_context)
                if hasattr(fixture_context, 'globs'):
                    globs = fixture_context.globs(globs)
            parser = doctest.DocTestParser()
            test = parser.get_doctest(
                doc, globs=globs, name=name,
                filename=filename, lineno=0)
            if test.examples:
                case = DocFileCase(
                    test,
                    setUp=getattr(fixture_context, 'setup_test', None),
                    tearDown=getattr(fixture_context, 'teardown_test', None),
                    result_var=self.doctest_result_var)
                if fixture_context:
                    yield ContextSuite(tests=(case,), context=fixture_context)
                else:
                    yield case
            else:
                yield False # no tests to load
            
    def makeTest(self, obj, parent):
        """Look for doctests in the given object, which will be a
        function, method or class.
        """
        name = getattr(obj, '__name__', 'Unnammed %s' % type(obj))
        doctests = self.finder.find(obj, module=getmodule(parent), name=name)
        if doctests:
            for test in doctests:
                if len(test.examples) == 0:
                    continue
                yield DocTestCase(test, obj=obj,
                                  result_var=self.doctest_result_var)
    
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
    """Overrides DocTestCase to
    provide an address() method that returns the correct address for
    the doctest case. To provide hints for address(), an obj may also
    be passed -- this will be used as the test object for purposes of
    determining the test address, if it is provided.    
    """
    def __init__(self, test, optionflags=0, setUp=None, tearDown=None,
                 checker=None, obj=None, result_var='_'):
        self._result_var = result_var
        self._nose_obj = obj
        super(DocTestCase, self).__init__(
            test, optionflags=optionflags, setUp=setUp, tearDown=tearDown,
            checker=checker)
    
    def address(self):
        if self._nose_obj is not None:
            return test_address(self._nose_obj)
        obj = resolve_name(self._dt_test.name)

        if isproperty(obj):
            # properties have no connection to the class they are in
            # so we can't just look 'em up, we have to first look up
            # the class, then stick the prop on the end
            parts = self._dt_test.name.split('.')
            class_name = '.'.join(parts[:-1])
            cls = resolve_name(class_name)
            base_addr = test_address(cls)
            return (base_addr[0], base_addr[1],
                    '.'.join([base_addr[2], parts[-1]]))
        else:
            return test_address(obj)
    
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

    def setUp(self):
        if self._result_var is not None:
            self._old_displayhook = sys.displayhook
            sys.displayhook = self._displayhook
        super(DocTestCase, self).setUp()

    def _displayhook(self, value):
        if value is None:
            return
        setattr(__builtin__, self._result_var,  value)
        print repr(value)

    def tearDown(self):
        super(DocTestCase, self).tearDown()
        if self._result_var is not None:
            sys.displayhook = self._old_displayhook
            delattr(__builtin__, self._result_var)


class DocFileCase(doctest.DocFileCase):
    """Overrides to provide address() method that returns the correct
    address for the doc file case.
    """
    def __init__(self, test, optionflags=0, setUp=None, tearDown=None,
                 checker=None, result_var='_'):
        self._result_var = result_var
        super(DocFileCase, self).__init__(
            test, optionflags=optionflags, setUp=setUp, tearDown=tearDown,
            checker=None)

    def address(self):
        return (self._dt_test.filename, None, None)

    def setUp(self):
        if self._result_var is not None:
            self._old_displayhook = sys.displayhook
            sys.displayhook = self._displayhook
        super(DocFileCase, self).setUp()

    def _displayhook(self, value):
        if value is None:
            return
        setattr(__builtin__, self._result_var, value)
        print repr(value)

    def tearDown(self):
        super(DocFileCase, self).tearDown()
        if self._result_var is not None:
            sys.displayhook = self._old_displayhook
            delattr(__builtin__, self._result_var)


def run(*arg, **kw):
    """DEPRECATED: moved to nose.plugins.plugintest.
    """
    import warnings
    warnings.warn("run() has been moved to nose.plugins.plugintest. Please "
                  "update your imports.", category=DeprecationWarning,
                  stacklevel=2)
    from nose.plugins.plugintest import run
    run(*arg, **kw)
