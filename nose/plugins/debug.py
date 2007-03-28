import pdb
from nose.plugins.base import Plugin

class Pdb(Plugin):
    enabled_for_failures = False

    def addError(self, test, err):
        ec, ev, tb = err
        pdb.post_mortem(tb)

    def addFailure(self, test, err):
        if not self.enabled_for_failures:
            return
        ec, ev, tb = err
        pdb.post_mortem(tb)
