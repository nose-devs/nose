import sys
from optparse import OptionParser
from nose.config import Config
from nose.plugins.cover import Coverage
from nose.tools import eq_
import unittest


class TestCoveragePlugin(object):

    def test_cover_options_package(self):
        _test_options_helper('--cover-package', 'coverPackages',
                             ['pkg1', 'pkg2', 'pkg3'], [],
                             'pkg1,pkg2,pkg3', 'NOSE_COVER_PACKAGE')

    def test_cover_options_erase(self):
        _test_options_helper('--cover-erase', 'coverErase',
                             True, False,
                             env_key='NOSE_COVER_ERASE')

    def test_cover_tests(self):
        _test_options_helper('--cover-tests', 'coverTests',
                             True, False,
                             env_key='NOSE_COVER_TESTS')

    def test_cover_config_file(self):
        c1, c2 = _test_options_helper('--cover-config-file', 'coverConfigFile',
                                      'not_default_config_file', True,
                                      arg_value='not_default_config_file',
                                      env_key='NOSE_COVER_CONFIG_FILE')

        cov_info = c1.coverInstance.sysinfo()
        for key, value in cov_info:
            if key == 'config_files':
                eq_(value, ['.coveragerc'])
                break
        else:
            assert False, "coverage did not load default config file"

        cov_info = c2.coverInstance.sysinfo()
        for key, value in cov_info:
            if key == 'config_files':
                eq_(value, ['not_default_config_file'])
                break
        else:
            assert False, "coverage did not load expected config file"


def _test_options_helper(arg_option, cover_option,
                         expected_set, expected_not_set,
                         arg_value=None, env_key=None):
    prefix_args = ['test_can_be_disabled', '--with-coverage']

    # Assert that the default works as expected
    parser = OptionParser()
    c_arg_not_set = Coverage()
    c_arg_not_set.addOptions(parser)
    options, _ = parser.parse_args(prefix_args)
    c_arg_not_set.configure(options, Config())
    eq_(expected_not_set, getattr(c_arg_not_set, cover_option))

    # Assert that the argument parser picks up the expected value
    parser = OptionParser()
    c_arg_set = Coverage()
    c_arg_set.addOptions(parser)

    if arg_value is None:
        args = arg_option
    else:
        args = arg_option + "=" + arg_value

    options, _ = parser.parse_args(prefix_args + [args])
    c_arg_set.configure(options, Config())
    eq_(expected_set, getattr(c_arg_set, cover_option))

    # If the option supports environment variables, check that too
    if env_key is not None:
        if arg_value is None:
            args = 'true'
        else:
            args = arg_value

        env = {env_key: args}
        c = Coverage()
        parser = OptionParser()
        c.addOptions(parser, env)
        options, _ = parser.parse_args(prefix_args)
        c.configure(options, Config())
        eq_(expected_set, getattr(c, cover_option))

    return c_arg_not_set, c_arg_set
