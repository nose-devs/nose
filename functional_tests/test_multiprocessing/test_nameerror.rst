    >>> from os.path import join, dirname
    >>> from nose.plugins.plugintest import run_buffered
    >>> from nose.plugins.multiprocess import MultiProcess

    >>> def run(*cmd): run_buffered(argv=list(cmd), plugins=[MultiProcess()])
    >>> def path(fname): return join(dirname(__file__), 'support', fname)

    >>> run( 'nosetests', '--processes=2', path('nameerror.py') )
    E
    ======================================================================
    ERROR: Failure: NameError (name 'undefined_variable' is not defined)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    NameError: name 'undefined_variable' is not defined
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    FAILED (errors=1)

