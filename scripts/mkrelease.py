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
svn_base_url = 'https://python-nose.googlecode.com/svn'
svn_trunk_url = 'https://python-nose.googlecode.com/svn/trunk'
svn_tags_url = 'https://python-nose.googlecode.com/svn/tags'

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
    tag = 'nose_rel_%s' % version
    svn_tag_url = "%s/%s" % (svn_tags_url, tag)

    # create tag
    runcmd("svn copy %s %s -m 'Tagged release %s'" %
           (svn_trunk_url, svn_tag_url, version))
    
    # check out tag
    cd('/tmp')
    runcmd('svn co %s' % svn_tag_url)
    cd(tag)

    # remove dev tag from setup
    runcmd('cp setup.cfg.release setup.cfg')
    runcmd('svn rm setup.cfg.release --force')
    runcmd("svn ci -m 'Updated setup.cfg to release status'")
    runcmd("rm -rf /tmp/%s" % tag)
    
    # need to build dist from an *export* to limit files included
    # (setuptools includes too many files when run under a checkout)

    # export tag
    cd('/tmp')
    runcmd('svn export %s %s' % (svn_tag_url, tag))
    cd(tag)

    # make docs
    #runcmd('./scripts/mkindex.py')
    cd('doc')
    runcmd('make html')
    cd('..')

    # make sdist
    runcmd('python setup.py sdist')

    # upload docs and distribution
    if 'NOSE_UPLOAD' in os.environ:
        up = os.environ['NOSE_UPLOAD']
        cv = {
            'host': up[:up.index(':')],
            'path': up[up.index(':')+1:-1],
            'version':version,
            'upload': up,
            'upload_docs': "%s/%s" % (up, version) }
        cv['versionpath'] = "%(path)s/%(version)s" % cv
        cv['docpath'] = "%(versionpath)s/doc" % cv

        cmd = 'scp -C dist/nose-%(version)s.tar.gz %(upload)s' % cv
        runcmd(cmd)

        cmd = 'ssh %(host)s "mkdir -p %(docpath)s"' % cv
        runcmd(cmd)
        
        #cmd = 'scp -C index.html %(upload_docs)s' % cv
        #runcmd(cmd)

        cmd = ('scp -C doc/*.html doc/*.css doc/*.png '
               '%(upload_docs)s/doc' % cv)
        runcmd(cmd)

        cmd = ('ssh %(host)s '
               'ln -nfs %(docpath)s %(path)s/doc"; '
               '"ln -nfs %(path)s/doc/main_index.html %(path)s/index.html'
                % cv)
        runcmd(cmd)

if __name__ == '__main__':
    main()
