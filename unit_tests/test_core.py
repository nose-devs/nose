import unittest
import nose.core
from nose.config import Config

from cStringIO import StringIO

class nullLoader:
    def loadTestsFromNames(self, names):
        return unittest.TestSuite()

class TestAPI_run(unittest.TestCase):

    def test_restore_stdout(self):
        import sys
        s = StringIO()
        stdout = sys.stdout
        conf = Config(stream=s, exit=False)
        res = nose.core.run(
            testLoader=nullLoader(), argv=['test_run'], env={}, config=conf)
        stdout_after = sys.stdout
        self.assertEqual(stdout, stdout_after)
        
if __name__ == '__main__':
    unittest.main()
