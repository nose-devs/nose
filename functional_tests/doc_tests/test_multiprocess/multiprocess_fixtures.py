from nose.plugins.skip import SkipTest

_multiprocess_can_split_ = True

def setup_module():
    try:
        import processing
    except ImportError:
        raise SkipTest("processing module not available")
