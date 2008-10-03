#!/bin/sh

echo "python 2.3..."
python2.3 selftest.py

echo
echo "python 2.4..."
python2.4 selftest.py

echo
echo "python 2.5..."
python2.5 selftest.py

echo
echo "python 2.6..."
python2.6 selftest.py

if [ "${JYTHON}x" != "x" ] 
then
    echo
    echo "jython..."
    $JYTHON selftest.py
else
    echo
    echo '$JYTHON not set'
    echo 'set $JYTHON to run selftest under jython'
    echo 'example: '
    echo "  export JYTHON='java -Dpython.home=<path>/dist/ -jar <path>/dist/jython.jar'"
    echo 'see http://wiki.python.org/jython/JythonDeveloperGuide'
fi
