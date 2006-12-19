"""Exceptions for marking tests as skipped or deprecated.
"""
class DeprecatedTest(Exception):
    """Raise this exception to mark a test as deprecated.
    """
    pass

class SkipTest(Exception):
    """Raise this exception to mark a test as skipped.
    """
    pass
