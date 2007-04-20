import re
import os
import tempfile
import unittest
import nose.config
import sys
from nose.core import configure, TestProgram as _TestProgram

# Configparser behaves differently under 2.3
compat_24 = sys.version_info >= (2, 4)

class InactiveTestProgram(_TestProgram):
    """
    A TestProgram subclass that doesn't automatically run tests when
    instantiated.
    """

    def createTests(self):
        pass

    def runTests(self):
        pass


class TestNoseConfig(unittest.TestCase):

    def test_defaults(self):
        c = nose.config.Config()
        assert c.addPaths == True
        assert c.capture == True
        assert c.detailedErrors == False
        # FIXME etc
        
    def test_reset(self):
        c = nose.config.Config()
        c.include = 'include'        
        assert c.include == 'include'
        c.reset()
        assert c.include is None

    def test_update(self):
        c = nose.config.Config()
        c.update({'exclude':'x'})
        assert c.exclude == 'x'

    def test_multiple_include(self):
        conf = configure(['--include=a', '--include=b'])
        self.assertEqual(conf.include, [re.compile('a'), re.compile('b')])

    def test_single_include(self):
        conf = configure(['--include=b'])
        self.assertEqual(conf.include, [re.compile('b')])


class TestNoseConfigFile(unittest.TestCase):

    def setUp(self):
        self.tp = InactiveTestProgram(argv=[], env={})
        self.first_arg = object()
        self.last_args = [object() for i in range(3)]
        self.argv = [self.first_arg] + self.last_args
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            try:
                os.remove(f)
            except OSError:
                pass

    def check_argv(self, expected_new_args):
        self.assertEqual(self.argv[0], self.first_arg)
        self.assertEqual(self.argv[-len(self.last_args):], self.last_args)
        self.assertEqual(self.argv[1:-len(self.last_args)], expected_new_args)

    def create_file(self, contents):
        path = tempfile.mktemp(prefix="nose")
        self.temp_files.append(path)
        f = open(path, "wb")
        f.write(contents)
        f.close()
        return path

    def test_no_files(self):
        parsed = self.tp.parseUserConfig(self.argv, [])
        if compat_24:
            self.assertEqual(parsed, [])
        self.check_argv([])

    def test_empty_files(self):
        f1 = self.create_file("[nosetests]")
        f2 = self.create_file("[nosetests]")
        parsed = self.tp.parseUserConfig(self.argv, [f1, f2])
        if compat_24:
            self.assertEqual(parsed, [f1, f2])
        self.check_argv([])

    def test_missing_file(self):
        f1 = tempfile.mktemp()
        f2 = self.create_file("[DEFAULT]\n[nosetests]\nverbosity=3\n")
        parsed = self.tp.parseUserConfig(self.argv, [f1, f2])
        if compat_24:
            self.assertEqual(parsed, [f2])
        self.check_argv(["--verbosity", "3"])

    def test_more_config(self):
        f1 = self.create_file("[nosetests]\nstop=True\n")
        f2 = self.create_file("[nosetests]\npdb=FALSE\n")
        parsed = self.tp.parseUserConfig(self.argv, [f1, f2])
        if compat_24:
            self.assertEqual(parsed, [f1, f2])
        self.check_argv(["--stop"])


if __name__ == '__main__':
    unittest.main()
