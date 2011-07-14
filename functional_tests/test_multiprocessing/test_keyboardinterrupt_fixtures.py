
def setup_module():
    try:
        import multiprocessing
    except ImportError:
        from nose.plugins.skip import SkipTest
        raise SkipTest("multiprocessing module not available")

