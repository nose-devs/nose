import os

from test_multiprocessing import MPTestBase

class TestConcurrentShared(MPTestBase):
    processes = 2
    suitepath = os.path.join(os.path.dirname(__file__), 'support',
                             'concurrent_shared')

    def runTest(self):
        assert 'Ran 2 tests in 1.' in self.output, "make sure two tests use 1.x seconds (no more than 2 seconsd)"
        assert str(self.output).strip().endswith('OK')

