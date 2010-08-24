#!/bin/sh

if [ -e "`which tox`" ]; then
    tox $@
else
    echo "**** install tox globally to test all Pythons at once http://codespeak.net/tox/"
    exec ./selftest.py $@
fi