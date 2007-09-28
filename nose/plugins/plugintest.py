"""
Plugin tester
-------------

Utilities for testing plugins.

See also `nose.plugins.doctests`_, which contains a version of `nose.run()`
that is useful for writing doctests about nose runs.

"""

import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    
__all__ = ['PluginTester']


class PluginTester(object):
    """A mixin for testing nose plugins in their runtime environment.
    
    Subclass this and mix in unittest.TestCase to run integration/functional 
    tests on your plugin.  When setUp() is called, the stub test suite is 
    executed with your plugin so that during an actual test you can inspect the 
    artifacts of how your plugin interacted with the stub test suite.
    
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
    
    - args
  
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
        """returns a suite object of tests to run (unittest.TestSuite())
        
        If self.suitepath is None, this must be implemented. The returned suite 
        object will be executed with all plugins activated.  It may return 
        None.
        
        Here is an example of a basic suite object you can return ::
        
            >>> import unittest
            >>> class SomeTest(unittest.TestCase):
            ...     def runTest(self):
            ...         raise ValueError("Now do something, plugin!")
            ... 
            >>> unittest.TestSuite([SomeTest()]) # doctest: +ELLIPSIS
            <unittest.TestSuite tests=[<...SomeTest testMethod=runTest>]>
        
        """
        raise NotImplementedError
    
    def _execPlugin(self):
        """execute the plugin on the internal test suite.
        """
        from nose.config import Config
        from nose.core import TestProgram
        from nose.plugins.manager import PluginManager
        
        suite = None
        stream = StringIO()
        conf = Config(env=self.env,
                      stream=stream,
                      plugins=PluginManager(plugins=self.plugins))
        if not self.suitepath:
            suite = self.makeSuite()
            
        self.nose = TestProgram(argv=self.argv, config=conf, suite=suite,
                                exit=False)
        self.output = AccessDecorator(stream)
                                
    def setUp(self):
        """runs nosetests with the specified test suite, all plugins 
        activated.
        """
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
