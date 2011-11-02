import os

from . import support, MPTestBase


#test case for #462
class TestClassFixture(MPTestBase):
    suitepath = os.path.join(support, 'class.py')

    def runTest(self):
        assert str(self.output).strip().endswith('OK')
        assert 'Ran 2 tests' in self.output

