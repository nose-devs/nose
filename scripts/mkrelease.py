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
parts = here.split('/')
svn = parts.index('svn')
svnroot = os.path.join('/', *parts[:svn+1])
branchroot = os.path.join(svnroot, 'branches')
tagroot = os.path.join(svnroot, 'tags')
svntrunk = os.path.join(svnroot, 'trunk')
svn_trunk_url = 'https://python-nose.googlecode.com/svn/trunk'

def runcmd(cmd):
    print cmd
    (status,output) = getstatusoutput(cmd)
    if status != success:
        raise Exception(output)

version = nose.__version__
versioninfo = nose.__versioninfo__

os.chdir(svnroot)
print "cd %s" % svnroot

# FIXME tail of version is hardcoded
branch = 'branches/%s.%s.0-stable' % (versioninfo[0], versioninfo[1])
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
    runcmd('svn copy %s %s' % (svn_trunk_url, branch))

    # clean up setup.cfg and check in branch
    os.chdir(branch)
    print "cd %s" % branch

    # remove dev tag from setup
    runcmd('cp setup.cfg.release setup.cfg')
    runcmd('svn rm setup.cfg.release --force')

    os.chdir(branchroot)
    print "cd %s" % branchroot
    runcmd("svn ci -m 'Release branch for %s'" % version)

else:
    # re-releasing branch
    os.chdir(branch)
    print "cd %s" % branch
    runcmd('svn up')
    os.chdir(svnroot)
    print "cd %s"% svnroot

# make tag from branch
print "cd %s" % svnroot
os.chdir(svnroot)
runcmd('svn copy %s %s' % (branch, tag))

# check in tag
os.chdir(tagroot)
print "cd %s" % tagroot
runcmd("svn ci -m 'Release tag for %s'" % version)

# make docs
os.chdir(svnroot)
os.chdir(tag)
print "cd %s" % tag

runcmd('scripts/mkindex.py')
runcmd('scripts/mkdocs.py')
# runcmd('scripts/mkwiki.py')

# setup sdist
runcmd('python setup.py sdist')

# upload docs and distribution
if 'NOSE_UPLOAD' in os.environ and False:
    cv = {'version':version,
          'upload': os.environ['NOSE_UPLOAD'],
          'upload_docs': "%s/%s" % (os.environ['NOSE_UPLOAD'], version) }
    cmd = 'scp -C dist/nose-%(version)s.tar.gz %(upload)s' % cv
    runcmd(cmd)

    cmd = 'scp -Cr index.html doc %(upload_docs)s' % cv
    runcmd(cmd)
    
os.chdir(current)
