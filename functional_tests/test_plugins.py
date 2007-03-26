import os
import sys
import unittest
from nose.config import Config
from nose.core import TestProgram

here = os.path.abspath(os.path.dirname(__file__))
support = os.path.join(here, 'support')
units = os.path.normpath(os.path.join(here, '..', 'unit_tests'))

if units not in sys.path:
    sys.path.insert(0, units)
from mock import RecordingPluginManager


class TestPluginCalls(unittest.TestCase):
    """
    Tests how plugins are called throughout a standard test run
    """
    def test_plugin_calls_package1(self):
        wdir = os.path.join(support, 'package1')
        man = RecordingPluginManager()
        conf = Config(exit=False, plugins=man)
        t = TestProgram(defaultTest=wdir, config=conf)
        print man.called
        assert man.called


if __name__ == '__main__':
    unittest.main()
