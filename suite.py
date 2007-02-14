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


class ContextSuiteFactory(object):
    def __init__(self, context):
        self.context = context

    def __call__(self, tests):
        print "Building a context suite for %s" % tests
        return ContextSuite(lambda: tests, self.context)


class ContextSuite(LazySuite):
    def __init__(self, test_generator, context):
        self.context = context
        LazySuite.__init__(self, test_generator)
        
    def _get_tests_with_context(self):
        for test in self._get_tests():
            yield self.context(test)

    _tests = property(_get_tests_with_context, LazySuite._set_tests, None,
                      "Access the tests in this suite. Tests are returned "
                      "inside of a context wrapper that controls when "
                      "module-level fixtures execute.")
