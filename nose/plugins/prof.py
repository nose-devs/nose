"""Use the profile plugin with --with-profile or NOSE_WITH_PROFILE to
enable profiling using the hotshot profiler. Profiler output can be
controlled with the --profile-sort and --profile-restrict, and the
profiler output file may be changed with --profile-stats-file.

See the hotshot documentation in the standard library documentation for
more details on the various output options.
"""

import hotshot, hotshot.stats
import logging
import os
import sys
import tempfile
from nose.plugins.base import Plugin
from nose.util import tolist

log = logging.getLogger('nose.plugins')

class Profile(Plugin):
    """
    Use this plugin to run tests using the hotshot profiler. 
    """
    def add_options(self, parser, env=os.environ):
        Plugin.add_options(self, parser, env)                
        parser.add_option('--profile-sort',action='store',dest='profile_sort',
                          default=env.get('NOSE_PROFILE_SORT','cumulative'),
                          help="Set sort order for profiler output")
        parser.add_option('--profile-stats-file',action='store',
                          dest='profile_stats_file',
                          default=env.get('NOSE_PROFILE_STATS_FILE'),
                          help='Profiler stats file; default is a new '
                          'temp file on each run')
        parser.add_option('--profile-restrict',action='append',
                          dest='profile_restrict',
                          default=env.get('NOSE_PROFILE_RESTRICT'),
                          help="Restrict profiler output. See help for "
                          "pstats.Stats for details")
    
    def begin(self):
        self.prof = hotshot.Profile(self.pfile)

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.options = options
        self.conf = conf

        if options.profile_stats_file:
            self.pfile = options.profile_stats_file
        else:
            fileno, filename = tempfile.mkstemp()
            # close the open handle immediately, hotshot needs to open
            # the file itself
            os.close(fileno)
            self.pfile = filename
        self.sort = options.profile_sort
        self.restrict = tolist(options.profile_restrict)
            
    def prepareTest(self, test):
        log.debug('preparing test %s' % test)
        def run_and_profile(result, prof=self.prof, test=test):
            prof.runcall(test, result)
        return run_and_profile
        
    def report(self, stream):
        log.debug('printing profiler report')
        self.prof.close()
        stats = hotshot.stats.load(self.pfile)
        stats.sort_stats(self.sort)
        try:
            tmp = sys.stdout
            sys.stdout = stream
            if self.restrict:
                log.debug('setting profiler restriction to %s', self.restrict)
                stats.print_stats(*self.restrict)
            else:
                stats.print_stats()
        finally:
            sys.stdout = tmp
