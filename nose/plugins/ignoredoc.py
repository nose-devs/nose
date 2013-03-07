"""
If this plugin is active, nose doesn't use docstrings to name tests.
"""

from nose.plugins.base import Plugin


class IgnoreDocstrings(Plugin):
    """
    Don't use docstrings to name tests.
    """

    name = 'ignore-docstrings'

    def describeTest(self, test):
        return str(test)
