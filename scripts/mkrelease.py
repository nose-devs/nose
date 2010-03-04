#!/usr/bin/env python
#
#
# create and upload a release
import os
import nose
import sys
from commands import getstatusoutput

success = 0

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
            raise Exception(output)


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

    # build included docs
    cd('doc')
    runcmd('make man readme html')
    cd('..')

    # make the distribution
    runcmd('python setup.py sdist')

    # upload docs and distribution
    if 'NOSE_UPLOAD' in os.environ:
        up = os.environ['NOSE_UPLOAD']
        cv = {
            'host': up[:up.index(':')],
            'path': up[up.index(':')+1:-1],
            'version':version,
            'upload': up,
            'upload_docs': os.path.join(up, version) }
        cv['versionpath'] = os.path.join(cv['path'], cv['version'])

        cmd = 'scp -C dist/nose-%(version)s.tar.gz %(upload)s' % cv
        runcmd(cmd)

        cmd = 'ssh %(host)s "mkdir -p %(versionpath)s"' % cv
        runcmd(cmd)

        cmd = ('scp -Cr doc/.build/html/* '
               '%(upload_docs)s/' % cv)
        runcmd(cmd)

        cmd = ('scp -C doc/index.html %(upload)s' % cv)
        runcmd(cmd)

if __name__ == '__main__':
    main()
