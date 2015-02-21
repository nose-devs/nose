import unittest

class TestForXunit(unittest.TestCase):
    @unittest.expectedFailure
    def test_expected_failure(self):
        self.assertEqual("this", "that")

    @unittest.expectedFailure
    def test_unexpected_success(self):
        pass
