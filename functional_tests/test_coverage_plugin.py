"""Test the coverage plugin."""
import os
import unittest
import shutil

from nose.plugins import PluginTester
from nose.plugins.cover import Coverage

support = os.path.join(os.path.dirname(__file__), 'support')


class TestCoveragePlugin(PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-html']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage')

    def setUp(self):
        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        super(TestCoveragePlugin, self).setUp()

    def runTest(self):
        self.assertTrue("blah        4      1    75%   6" in self.output)
        self.assertTrue("Ran 1 test in""" in self.output)
        # Assert coverage html report exists
        self.assertTrue(os.path.exists(os.path.join(self.cover_html_dir,
            'index.html')))
        # Assert coverage data is saved
        self.assertTrue(os.path.exists(self.cover_file))

if __name__ == '__main__':
    unittest.main()
