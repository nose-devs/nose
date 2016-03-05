import os
import sys
import unittest
from subprocess import PIPE, Popen

import nose
from nose.plugins.skip import SkipTest


support = os.path.join(os.path.dirname(__file__), 'support', 'issue879')

class TestIssue879(unittest.TestCase):
    def setUp(self):
        try:
            import setuptools
        except ImportError:
            raise SkipTest("setuptools not available")
        os.chdir(support)

    def test_command_can_ignore_user_config_files(self):
        pythonpath = os.path.normpath(os.path.join(
            os.path.abspath(os.path.dirname(nose.__file__)),
            '..'))

        env = {
            'HOME': support,
            'PYTHONPATH': pythonpath
            }
        process = Popen(
            [sys.executable, 'setup.py', 'nosetests'],
            stdout=PIPE, stderr=PIPE, env=env)
        out, err = process.communicate()
        retcode = process.poll()
        self.assertNotEqual(retcode, 0)
        err = err.decode(sys.stderr.encoding)
        self.assertTrue("no such option 'fail'" in err)

        env = {
            'HOME': support,
            'PYTHONPATH': pythonpath,
            'NOSE_IGNORE_CONFIG_FILES': '1'
            }
        process = Popen(
            [sys.executable, 'setup.py', 'nosetests'],
            stdout=PIPE, stderr=PIPE, env=env)
        out, err = process.communicate()
        retcode = process.poll()
        self.assertEqual(retcode, 0)


if __name__ == '__main__':
    unittest.main()
