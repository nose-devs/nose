#!/bin/sh

if [ -e "`which tox`" ]; then
    tox $@
else
    echo "**** install tox globally to test all Pythons at once http://codespeak.net/tox/"
    python setup.py egg_info
    python selftest.py $@
fi