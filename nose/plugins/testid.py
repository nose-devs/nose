import logging
import os
from nose.plugins import Plugin

try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

log = logging.getLogger(__name__)

class TestId(Plugin):
    """
    Activate to add a test id (like #1) to each test name
    output. Once you've run once to generate test ids, you can re-run
    individual tests by activating the plugin and passing the ids
    instead of test names.
    """
    name = 'id'
    idfile = None
    shouldSave = True
    
    def options(self, parser, env):
        Plugin.options(self, parser, env)
        parser.add_option('--id-file', action='store', dest='testIdFile',
                          default='~/.noseids',
                          help="Store test ids found in test runs in this "
                          "file.")

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.idfile = os.path.expanduser(options.testIdFile)
        self.id = 1
        self.ids = {}
        self.tests = {}
        # used to track ids seen when tests is filled from
        # loaded ids file
        self._seen = {}

    def finalize(self, result):
        if self.shouldSave:
            fh = open(self.idfile, 'w')
            ids = dict(zip(self.tests.values(), self.tests.keys()))            
            dump(ids, fh)
            fh.close()
            log.debug('Saved test ids: %s to %s', ids, self.idfile)

    def loadTestsFromNames(self, names, module=None):
        """Translate ids in the list of requested names into their
        test addresses, if they are found in my dict of tests.
        """
        log.debug('ltfn %s %s', names, module)
        try:
            fh = open(self.idfile, 'r')
            self.ids = load(fh)
            log.debug('Loaded test ids %s from %s', self.ids, self.idfile)
            fh.close()
        except IOError:
            log.debug('IO error reading %s', self.idfile)
            return
            
        # I don't load any tests myself, only translate names like '#2'
        # into the associated test addresses
        result = (None, map(self.tr, names))
        if not self.shouldSave:
            # got some ids in names, so make sure that the ids line
            # up in output with what I said they were last time
            self.tests = dict(zip(self.ids.values(), self.ids.keys()))
        return result

    def makeName(self, addr):
        log.debug("Make name %s", addr)
        filename, module, call = addr
        if filename is not None:
            base, ext = os.path.splitext(filename)
            if ext in ('.pyc', '.pyo'):
                ext = '.py'
            head = base + ext
        else:
            head = module
        if call is not None:
            return "%s:%s" % (head, call)
        return head
        
    def setOutputStream(self, stream):
        self.stream = stream

    def startTest(self, test):
        adr = test.address()
        if adr in self.tests:
            if self.shouldSave or adr in self._seen:
                self.stream.write('   ')
            else:
                self.stream.write('#%s ' % self.tests[adr])
                self._seen[adr] = 1
            return
        self.tests[adr] = self.id
        self.stream.write('#%s ' % self.id)
        self.id += 1

    def tr(self, name):
        log.debug("tr '%s'", name)
        if name.startswith('#'):
            try:
                key = int(name.replace('#', ''))
            except ValueError:
                return name
            log.debug("Got key %s", key)
            self.shouldSave = False
            if key in self.ids:
                return self.makeName(self.ids[key])
        return name
        
