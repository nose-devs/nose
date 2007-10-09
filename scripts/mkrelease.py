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
version = nose.__version__
here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
parts = here.split('/')
branch = parts.index('branches')
svnroot = os.path.join('/', *parts[:branch])
branchroot = os.path.join(svnroot, 'branches')
tagroot = os.path.join(svnroot, 'tags')
svntrunk = os.path.join(svnroot, 'trunk')
svn_trunk_url = 'https://python-nose.googlecode.com/svn/trunk'

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
    cd(svnroot)
    branch = 'branches/%s-stable' % version
    tag =  'tags/%s-release' % version

    if os.path.isdir(tag):
        raise Exception(
            "Tag path %s already exists. Can't release same version twice!"
            % tag)

    # make branch, if needed
    if not os.path.isdir(branch):
        # update trunk
        cd(svntrunk)
        runcmd('svn up')
        cd(svnroot)
        runcmd('svn copy %s %s' % (svn_trunk_url, branch))

        # clean up setup.cfg and check in branch
        cd(branch)

        # remove dev tag from setup
        runcmd('cp setup.cfg.release setup.cfg')
        runcmd('svn rm setup.cfg.release --force')

        cd(branchroot)
        runcmd("svn ci -m 'Release branch for %s'" % version)

    else:
        # re-releasing branch
        cd(branch)
        runcmd('svn up')
        cd(svnroot)

    # make tag from branch
    cd(svnroot)
    runcmd('svn copy %s %s' % (branch, tag))

    # check in tag
    cd(tagroot)
    runcmd("svn ci -m 'Release tag for %s'" % version)

    # make docs
    cd(svnroot)
    cd(tag)

    runcmd('scripts/mkindex.py')
    runcmd('scripts/mkdocs.py')
    runcmd('scripts/mkwiki.py')

    # setup sdist
    runcmd('python setup.py sdist')

    # upload docs and distribution
    if 'NOSE_UPLOAD' in os.environ:
        up = os.environ['NOSE_UPLOAD']
        cv = {
            'host': up[:up.index(':')],
            'path': up[up.index(':')+1:],
            'version':version,
            'upload': up,
            'upload_docs': "%s%s" % (up, version) }
        cv['versionpath'] = "%(path)s%(version)s" % cv
        cv['docpath'] = "%(versionpath)s/doc" % cv

        cmd = 'scp -C dist/nose-%(version)s.tar.gz %(upload)s' % cv
        runcmd(cmd)

        cmd = 'ssh %(host)s "mkdir -p %(docpath)s"' % cv
        runcmd(cmd)
        
        cmd = 'scp -C index.html %(upload_docs)s' % cv
        runcmd(cmd)

        cmd = ('scp -C doc/*.html doc/*.css doc/*.png '
               '%(upload_docs)s/doc' % cv)
        runcmd(cmd)

        cmd = ('ssh %(host)s '
               '"ln -nfs %(versionpath)s/index.html %(path)s/index.html; '
               'ln -nfs %(docpath)s %(path)s/doc"' % cv)
        runcmd(cmd)
        
    cd(current)

if __name__ == '__main__':
    main()
