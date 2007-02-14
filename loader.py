import unittest
from suite import LazySuite

class TestLoader(unittest.TestLoader):
    def loadTestsFromNames(self, names, module=None):
        def load():
            for test in self.loadTestsFromName(name, module):
                yield test
        return LazySuite(load)
