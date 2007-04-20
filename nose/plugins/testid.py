import tempfile
import os
from nose.plugins import Plugin


class TestId(Plugin):
    name = 'id'
    idfile = None
    
    def options(self, parser, env):
        Plugin.options(self, parser, env)
        parser.add_option('--id-file', action='store', dest='testIdFile',
                          default='~/.testid',
                          help="Store test ids found in test runs in this "
                          "file.")

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.idfile = options.testIdFile
        self.id = 1
        self.tests = {}

    def setOutputStream(self, stream):
        self.stream = stream

    def startTest(self, test):
        adr = test.address()
        # FIXME account for up to thousands of tests with padding
        if adr in self.tests:
            self.stream.write('   ')
            return
        self.tests[adr] = self.id
        self.stream.write('#%s ' % self.id)
        self.id += 1
