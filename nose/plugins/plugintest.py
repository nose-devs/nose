
"""utilities for testing plugins"""

import os
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    
__all__ = ['PluginTester']

class PluginTester(object):
    """A mixin for testing nose plugins in their runtime environment.
    
    Subclass this and mix in unittest.TestCase to run integration/functional 
    tests on your plugin.  After setUp() the class contains an attribute, 
    self.nose, which is an instance of NoseStream.  See NoseStream docs for 
    more details
    
    Class Variables
    ---------------
    - activate_opt
    
      - the option to send nosetests to activate the plugin
     
    - suitepath
    
      - if set, this is the path of the suite to test.  otherwise, you
        will need to use the hook, makeSuite()
      
    - debuglog

      - if not None, becomes the value of --debug=debuglog
    
    - addargs
  
      - a list of arguments to add to the nosetests command
    
    - env
    
      - optional dict of environment variables to send nosetests
      
    """
    activate_opt = None
    suitepath = None
    debuglog = False
    addargs = None
    env = {}
    _args = None
    plugins = []
    
    def makeSuite(self):
        """must return the full path to a directory to test."""
        raise NotImplementedError

    
    def _execPlugin(self):
        """Create a TestProgram run with the given plugins, for
        the suite returned by makeSuite or found at suitePath
        """
        from nose.config import Config
        from nose.core import TestProgram
        from nose.plugins.manager import PluginManager
        
        suite = None
        stream = StringIO()
        conf = Config(exit=False,
                      stream=stream,
                      plugins=PluginManager(plugins=self.plugins))
        if not self.suitepath:
            suite = self.makeSuite()
            
        self.nose = TestProgram(argv=self._args, env=self.env,
                                config=conf, suite=suite)
        self.output = AccessDecorator(stream)
                                
    def setUp(self):
        """runs nosetests within a directory named self.suitepath
        """  
        if not self.env:  
            self.env = dict([(k,v) for k,v in os.environ.items()])
        self._args = ['nosetests', self.activate_opt]
        if self.addargs:
            self._args.extend(self.addargs)
        if self.debuglog:
            self._args.append('--debug=%s' % self.debuglog)
        if self.suitepath:
            self._args.append(self.suitepath)

        self._execPlugin()


class AccessDecorator(object):
    stream = None
    _buf = None
    def __init__(self, stream):
        self.stream = stream
        stream.seek(0)
        self._buf = stream.read()
        stream.seek(0)
    def __contains__(self, val):
        return val in self._buf
    def __iter__(self):
        return self.stream
    def __str__(self):
        return self._buf
