
"""utilities for testing plugins"""

import copy
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
    - activate
    
      - the argument to send nosetests to activate the plugin
     
    - suitepath
    
      - if set, this is the path of the suite to test.  otherwise, you
        will need to use the hook, makeSuite()
      
    - plugins

      - the list of plugins to make available during the run. Note
        that this does not mean these plugins will be *enabled* during
        the run -- only the plugins enabled by the activate argument
        or other settings in argv or env will be enabled.
    
    - argv
  
      - a list of arguments to add to the nosetests command, in addition to
        the activate argument
    
    - env
    
      - optional dict of environment variables to send nosetests
      
    """
    activate = None
    suitepath = None
    args = None
    env = {}
    argv = None
    plugins = []
    
    def makeSuite(self):
        """Must override to return a suite of tests to run if you
        don't supply a suitepath.
        """
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
            
        self.nose = TestProgram(argv=self.argv, env=self.env,
                                config=conf, suite=suite)
        self.output = AccessDecorator(stream)
                                
    def setUp(self):
        """runs nosetests within a directory named self.suitepath
        """
        if not self.env:  
            self.env = dict([(k,v) for k,v in os.environ.items()])
        self.argv = ['nosetests', self.activate]
        if self.args:
            self.argv.extend(self.args)
        if self.suitepath:
            self.argv.append(self.suitepath)            

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
