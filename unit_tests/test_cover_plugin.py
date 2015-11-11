from optparse import OptionParser
from nose.config import Config
from nose.plugins.cover import Coverage
from nose.tools import assert_false, assert_true, eq_


def _get_coverage_obj(args, env=None):
    parser = OptionParser()
    c = Coverage()
    c.addOptions(parser, env)
    options, args = parser.parse_args(['test_can_be_disabled'] + args)
    c.configure(options, Config())
    return c


class TestCoveragePlugin(object):

    def test_cover_packages_option(self):
        c = _get_coverage_obj(['--cover-package=pkg1,pkg2,pkg3'])
        eq_(['pkg1', 'pkg2', 'pkg3'], c.coverPackages)

        env = {'NOSE_COVER_PACKAGE': 'pkg1,pkg2,pkg3'}
        c = _get_coverage_obj([], env)
        eq_(['pkg1', 'pkg2', 'pkg3'], c.coverPackages)

    def test_want_file_inclusive(self):
        c = _get_coverage_obj(['--cover-inclusive'])
        assert_true(c.wantFile('pkg1/foo.py'))

        env = {'NOSE_COVER_INCLUSIVE': 'yes'}
        c = _get_coverage_obj([], env)
        assert_true(c.wantFile('pkg1/foo.py'))

    def test_want_file_inclusive_exclude(self):
        c = _get_coverage_obj(['--cover-inclusive',
                               '--cover-exclude-file=foo.py'])
        assert_false(c.wantFile('foo.py'))
        assert_true(c.wantFile('bar.py'))

        env = {'NOSE_COVER_INCLUSIVE': 'yes',
               'NOSE_COVER_EXCLUDE_FILE': 'foo.py'}
        c = _get_coverage_obj([], env)
        assert_false(c.wantFile('foo.py'))
        assert_true(c.wantFile('bar.py'))

    def test_want_file_inclusive_exclude_globs(self):
        c = _get_coverage_obj(['--cover-inclusive',
                               '--cover-exclude-file=foo/*.py'])
        assert_false(c.wantFile('foo/bar.py'))
        assert_true(c.wantFile('bar.py'))

        env = {'NOSE_COVER_INCLUSIVE': 'yes',
               'NOSE_COVER_EXCLUDE_FILE': 'foo/*.py'}
        c = _get_coverage_obj([], env)
        assert_false(c.wantFile('foo/bar.py'))
        assert_true(c.wantFile('bar.py'))

    def test_want_file_inclusive_multiple_args(self):
        c = _get_coverage_obj(['--cover-inclusive',
                               '--cover-exclude-file=foo.py',
                               '--cover-exclude-file=bar.py'])
        assert_false(c.wantFile('foo.py'))
        assert_false(c.wantFile('bar.py'))
        assert_true(c.wantFile('baz.py'))

        env = {'NOSE_COVER_INCLUSIVE': 'yes',
               'NOSE_COVER_EXCLUDE_FILE': 'bar.py,foo.py'}
        c = _get_coverage_obj([], env)
        assert_false(c.wantFile('foo.py'))
        assert_false(c.wantFile('bar.py'))
        assert_true(c.wantFile('baz.py'))
