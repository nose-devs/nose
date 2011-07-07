    >>> from os.path import join, dirname
    >>> from nose.plugins.plugintest import run_buffered
    >>> from nose.plugins.multiprocess import MultiProcess

    >>> run_buffered( argv=[
    ...         'nosetests', '--processes=2', '--process-timeout=1',
    ...         join(dirname(__file__), 'support', 'timeout.py') 
    ... ], plugins=[MultiProcess()])
    E
    ======================================================================
    ERROR: this test *should* fail when process-timeout=1
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    TimedOutException: 'timeout.test_timeout'
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    FAILED (errors=1)

    >>> run_buffered( argv=[
    ...         'nosetests', '--processes=2', '--process-timeout=3',
    ...         join(dirname(__file__), 'support', 'timeout.py') 
    ... ], plugins=[MultiProcess()])
    .
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    OK


