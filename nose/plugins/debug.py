"""
This plugin provides --pdb and --pdb-failures options that cause the
test runner to drop into pdb if it encounters an error or failure,
respectively.
"""

import os
import pdb
from nose.plugins.base import Plugin

class Pdb(Plugin):
    """
    Provides --pdb and --pdb-failures options that cause the test runner to
    drop into pdb if it encounters an error or failure, respectively.
    """
    enabled_for_errors = False
    enabled_for_failures = False
    score = 5 # run last, among builtins
    
    def options(self, parser, env=os.environ):
        parser.add_option(
            "--pdb", action="store_true", dest="debugErrors",
            default=env.get('NOSE_PDB', False),
            help="Drop into debugger on errors")
        parser.add_option(
            "--pdb-failures", action="store_true",
            dest="debugFailures",
            default=env.get('NOSE_PDB_FAILURES', False),
            help="Drop into debugger on failures")

    def configure(self, options, conf):
        self.conf = conf
        self.enabled = options.debugErrors or options.debugFailures
        self.enabled_for_errors = options.debugErrors
        self.enabled_for_failures = options.debugFailures

    def addError(self, test, err):
        if not self.enabled_for_errors:
            return
        self.debug(err)

    def addFailure(self, test, err):
        if not self.enabled_for_failures:
            return
        self.debug(err)

    def debug(self, err):
        import sys
        ec, ev, tb = err
        stdout = sys.stdout
        sys.stdout = sys.__stdout__
        try:
            pdb.post_mortem(tb)
        finally:
            sys.stdout = stdout
