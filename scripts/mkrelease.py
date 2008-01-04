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
if 'branches' in parts:
    lindex = parts.index('branches')
elif 'tags' in parts:
    lindex = parts.index('tags')
elif 'trunk' in parts:
    lindex = parts.index('trunk')
else:
    raise Exception("Unable to find svnroot from %s" % here)
svnroot = os.path.join('/', *parts[:lindex])    
    
branchroot = os.path.join(svnroot, 'branches')
tagroot = os.path.join(svnroot, 'tags')
svntrunk = os.path.join(svnroot, 'trunk')
svn_base_url = 'https://python-nose.googlecode.com/svn'
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

    svn_branch_url = '%s/%s' % (svn_base_url, branch)
    svn_tag_url = '%s/%s' % (svn_base_url, tag)

    if os.path.isdir(tag):
        raise Exception(
            "Tag path %s already exists. Can't release same version twice!"
            % tag)

    # make branch, if needed
    if not os.path.isdir(os.path.join(svnroot, branch)):
        # make branch
        runcmd("svn copy %s %s -m 'Release branch for %s'"
               % (svn_trunk_url, svn_branch_url, version))
        # clean up setup.cfg and check in tag
        cd(branchroot)
        runcmd('svn co %s' % svn_branch_url)
    else:
        # re-releasing branch
        cd(branch)
        runcmd('svn up')

    # make tag from branch
    runcmd('svn copy %s %s -m "Release tag for %s"'
           % (svn_branch_url, svn_tag_url, version))

    # check out tag
    cd(tagroot)
    runcmd('svn co %s' % svn_tag_url)
    cd(svnroot)
    cd(tag)

    # remove dev tag from setup
    runcmd('cp setup.cfg.release setup.cfg')
    runcmd('svn rm setup.cfg.release --force')
    runcmd("svn ci -m 'Updated setup.cfg to release status'")

    # wiki pages must be built from tag checkout
    runcmd('./scripts/mkwiki.py')

    # need to build dist from an *export* to limit files included
    # (setuptools includes too many files when run under a checkout)

    # export tag
    cd('/tmp')
    runcmd('svn export %s nose_rel_%s' % (svn_tag_url, version))
    cd('nose_rel_%s' % version)

    # make docs
    runcmd('./scripts/mkindex.py')
    runcmd('./scripts/mkdocs.py')

    # make sdist
    runcmd('python setup.py sdist')

    # upload docs and distribution
    if 'NOSE_UPLOAD' in os.environ:
        up = os.environ['NOSE_UPLOAD']
        cv = {
            'host': up[:up.index(':')],
            'path': up[up.index(':')+1:],
            'version':version,
            'upload': up,
            'upload_docs': "%s/%s" % (up, version) }
        cv['versionpath'] = "%(path)s/%(version)s" % cv
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
