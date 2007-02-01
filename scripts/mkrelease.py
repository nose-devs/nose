#!/usr/bin/env python
#
#
# create and upload a release
import os
import nose
import sys
from commands import getstatusoutput

success = 0

current = os.getcwd()

here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
svnroot = os.path.abspath(os.path.dirname(here))
svntrunk = os.path.join(svnroot, 'trunk')

def runcmd(cmd):
    print cmd
    (status,output) = getstatusoutput(cmd)
    if status != success:
        raise Exception(output)

version = nose.__version__
versioninfo = nose.__versioninfo__

# old: runcmd('bzr branch . ../nose_dev-%s' % version)

os.chdir(svnroot)
print "cd %s" % svnroot

branch = 'branches/%s.%s.%s-stable' % (versioninfo[0],
                                       versioninfo[1], versioninfo[2])
tag =  'tags/%s-release' % version
if os.path.isdir(tag):
    raise Exception("Tag path %s already exists. Can't release same version "
                    "twice!")

# make branch, if needed
if not os.path.isdir(branch):
    # update trunk
    os.chdir(svntrunk)
    print "cd %s" % svntrunk
    runcmd('svn up')
    os.chdir(svnroot)
    print "cd %s" % svnroot    
    runcmd('svn copy trunk %s' % branch)
    base = 'trunk'
else:
    # re-releasing branch
    base = branch
    os.chdir(branch)
    print "cd %s" % branch
    runcmd('svn up')
    os.chdir(svnroot)
    print "cd %s"% svnroot
    
# make tag
runcmd('svn copy %s %s' % (base, tag))

if os.path.exists(os.path.join(branch, 'setup.cfg')):
    os.chdir(branch)
    print "cd %s" % branch
    runcmd('svn rm setup.cfg --force') # remove dev tag from setup
    print "cd %s" % svnroot
    os.chdir(svnroot)
    
os.chdir(tag)
print "cd %s" % tag
runcmd('svn rm setup.cfg --force') # remove dev tag from setup

# check in
os.chdir(svnroot)
print "cd %s" % svnroot
runcmd("svn ci -m 'Release branch/tag for %s'" % version)

# make docs
os.chdir(tag)
print "cd %s" % tag

runcmd('scripts/mkindex.py')
runcmd('scripts/mkwiki.py')

# setup sdist
runcmd('python setup.py sdist')

# upload index.html, new dist version, new branch
# link current to dist version
if os.environ.has_key('NOSE_UPLOAD'):
    cmd = ('scp -C dist/nose-%(version)s.tar.gz '
           'index.html %(upload)s') % {'version':version,
                                       'upload': os.environ['NOSE_UPLOAD'] }
    runcmd(cmd)
           
os.chdir(current)
