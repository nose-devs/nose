#!/usr/bin/env python2.6
#
#
# create and upload a release
import os
import sys
import urllib
from urllib2 import urlopen
from commands import getstatusoutput

success = 0

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import nose
version = nose.__version__

SIMULATE = 'exec' not in sys.argv
if SIMULATE:
    print("# simulated run: run as scripts/mkrelease.py exec "
          "to execute commands")


def runcmd(cmd):
    print cmd
    if not SIMULATE:
        (status,output) = getstatusoutput(cmd)
        if status != success:
            sys.stderr.write(output)
            sys.stderr.write("\n")
            raise Exception('command did not exit successfully')


def cd(dir):
    print "cd %s" % dir
    if not SIMULATE:
        os.chdir(dir)


def main():
    tag = 'release_%s' % version

    # create tag
    runcmd("hg tag -fm 'Tagged release %s' %s" %
           (version, tag))

    # clone a fresh copy
    runcmd('hg clone -r %s . /tmp/nose_%s' % (tag, tag))

    # build release in clone
    cd('/tmp/nose_%s' % tag)

    # remove dev tag from setup
    runcmd('cp setup.cfg.release setup.cfg')

    # build included docs, run tests
    runcmd('tox')

    # make the distributions
    runcmd('python setup.py sdist upload -s')
    # TODO(Kumar) put this back when this bug is fixed:
    # http://bugs.python.org/issue10571
    # runcmd('python3.2 setup.py bdist_egg upload -s')
    runcmd('python setup.py register')

    rtd = 'http://readthedocs.org/build/1137'
    print 'POST %s' % rtd
    if not SIMULATE:
        u = urlopen(rtd,
                    # send dummy params to force a POST
                    urllib.urlencode({'build': 1}))
        print u.read()
        u.close()

    print '*'
    print "* it's live! Now you can show/hide old releases on PyPI"
    print '*'

if __name__ == '__main__':
    main()
