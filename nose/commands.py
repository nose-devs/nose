"""
nosetests setuptools command
----------------------------

You can run tests using the `nosetests` setuptools command::

  python setup.py nosetests

This command has a few benefits over the standard `test` command: all nose
plugins are supported, and you can configure the test run with both command
line arguments and settings in your setup.cfg file.

To configure the `nosetests` command, add a [nosetests] section to your
setup.cfg. The [nosetests] section can contain any command line arguments that
nosetests supports. The differences between issuing an option on the command
line and adding it to setup.cfg are:

 * In setup.cfg, the -- prefix must be excluded
 * In setup.cfg, command line flags that take no arguments must be given an
   argument flag (1, T or TRUE for active, 0, F or FALSE for inactive)

Here's an example [nosetests] setup.cfg section::

  [nosetests]
  verbosity=1
  detailed-errors
  with-coverage=1
  cover-package=nose
  debug=nose.loader
  pdb=1
  pdb-failures=1

If you commonly run nosetests with a large number of options, using the
nosetests setuptools command and configuring with setup.cfg can make running
your tests much less tedious.
"""
import os
from setuptools import Command
from nose.core import get_parser, main


parser = get_parser(env={})


    
def get_user_options():
    """convert a optparse option list into a distutils option tuple list"""
    opt_list = []
    for opt in parser.option_list:
        if opt._long_opts[0][2:] in option_blacklist: 
            continue
        
        long_name = opt._long_opts[0][2:]
        if opt.action != 'store_true':
            long_name = long_name + "="
        
        short_name = None
        if opt._short_opts:
            short_name =  opt._short_opts[0][1:]

        opt_list.append((long_name, short_name, opt.help or ""))
        
    return opt_list


class nosetests(Command):
    description = "Run unit tests using nosetests"
    user_options = get_user_options()
    
    def initialize_options(self):
        """create the member variables, but change hyphens to underscores"""
        self.option_to_cmds = {}
        for opt in parser.option_list:
            cmd_name = opt._long_opts[0][2:]
            option_name = cmd_name.replace('-', '_')
            self.option_to_cmds[option_name] = cmd_name
            setattr(self, option_name, None)
        self.attr  = None
    
    def finalize_options(self):
        """nothing to do here"""
        pass
    
    def run(self):
        """ensure tests are capable of being run, then
        run nose.main with a reconstructed argument list"""
        self.run_command('egg_info')
        
        # Build extensions in-place
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')

        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)
        
        argv = [] 
        for (option_name, cmd_name) in self.option_to_cmds.items():
            if option_name in option_blacklist:
                continue
            value = getattr(self, option_name)
            if value is not None:
                if flag(value):
                    if _bool(value):
                        argv.append('--' + cmd_name)
                else:
                    argv.append('--' + cmd_name)
                    argv.append(value)
        main(argv=argv, env=os.environ)

