import unittest
from nose import case
from nose.plugins import Plugin, PluginManager

class Plug(Plugin):

    def loadTestsFromFile(self, path):
        class TC(unittest.TestCase):
            def test(self):
                pass
        return [TC('test')]

    def addError(self, test, err):
        return True

class Plug2(Plugin):

    def loadTestsFromFile(self, path):
        class TCT(unittest.TestCase):
            def test_2(self):
                pass
        return [TCT('test_2')]

    def addError(self, test, err):
        assert False, "Should not have been called"

class TestPluginManager(unittest.TestCase):

    def test_proxy_to_plugins(self):
        man = PluginManager(plugins=[Plug(), Plug2()])

        # simple proxy: first plugin to return a value wins
        self.assertEqual(man.addError(None, None), True)

        # multiple proxy: all plugins that return values get to run
        all = []
        for res in man.loadTestsFromFile('foo'):
            print res
            all.append(res)
        self.assertEqual(len(all), 2)


if __name__ == '__main__':
    unittest.main()
