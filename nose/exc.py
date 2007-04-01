"""Exceptions for marking tests as skipped or deprecated.
"""
from nose.plugins.skip import SkipTest

class DeprecatedTest(Exception):
    """Raise this exception to mark a test as deprecated.
    """
    pass
