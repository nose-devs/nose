    >>> import os
    >>> from nose.plugins.plugintest import run_buffered as run
    >>> from nose.plugins.testid import TestId
    >>> support = os.path.join(os.path.dirname(__file__), 'support', 'id_fails')
    >>> argv = [__file__, '-v', '--with-id', support]
    >>> run(argv=argv, plugins=[TestId()])
    #1 Failure: ImportError (No module named apackagethatdoesntexist) ... ERROR
    #2 test_b.test ... ok
    #3 test_b.test_fail ... FAIL
    <BLANKLINE>
    ======================================================================
    ERROR: Failure: ImportError (No module named apackagethatdoesntexist)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    ImportError: No module named apackagethatdoesntexist
    <BLANKLINE>
    ======================================================================
    FAIL: test_b.test_fail
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    AssertionError
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    FAILED (errors=1, failures=1)

Addressing failures works (sometimes).

    >>> argv.append('1')
    >>> run(argv=argv, plugins=[TestId()])
    #1 Failure: ImportError (No module named apackagethatdoesntexist) ... ERROR
    <BLANKLINE>
    ======================================================================
    ERROR: Failure: ImportError (No module named apackagethatdoesntexist)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    ImportError: No module named apackagethatdoesntexist
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    FAILED (errors=1)
