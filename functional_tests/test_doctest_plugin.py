import os
import unittest
from nose.plugins.doctests import Doctest
from nose.plugins import PluginTester

support = os.path.join(os.path.dirname(__file__), 'support')

class TestDoctestPlugin(PluginTester, unittest.TestCase):
    activate_opt = '--with-doctest'
    addargs = ['-v']
    plugins = [Doctest()]
    suitepath = os.path.join(support, 'dtt')
    
    def runTest(self):
        print str(self.output)

        assert 'Doctest: some_mod ... ok' in self.output
        assert 'Doctest: some_mod.foo ... ok' in self.output
        assert 'Ran 2 tests' in self.output
        assert str(self.output).strip().endswith('OK')

if __name__ == '__main__':
    unittest.main()
