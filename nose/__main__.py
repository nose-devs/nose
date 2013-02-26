import sys

from nose.core import run_exit

if sys.argv[0].endswith('__main__.py'):
    sys.argv[0] = 'python -m nose'

run_exit()
