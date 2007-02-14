import unittest

class LazySuite(unittest.TestSuite):

    def __init__(self, test_generator):
        self._tests = test_generator

    def _get_tests(self):
        for test in self.test_generator():
            yield test

    def _set_tests(self, test_generator):
        self.test_generator = test_generator

    _tests = property(_get_tests, _set_tests, None,
                      "Access the tests in this suite. Access is through a "
                      "generator, so iteration may not be repeatable.")
