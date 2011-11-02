import os

from . import support, MPTestBase

class TestMPTimeout(MPTestBase):
    args = ['--process-timeout=1']
    suitepath = os.path.join(support, 'timeout.py')

    def runTest(self):
        assert "TimedOutException: 'timeout.test_timeout'" in self.output
        assert "Ran 2 tests in" in self.output
        assert "FAILED (errors=1)" in self.output

class TestMPTimeoutPass(TestMPTimeout):
    args = ['--process-timeout=3']

    def runTest(self):
        assert "TimedOutException: 'timeout.test_timeout'" not in self.output
        assert "Ran 2 tests in" in self.output
        assert str(self.output).strip().endswith('OK')

