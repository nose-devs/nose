from nose import SkipTest
import sys

if sys.version_info >= (3,):
    raise SkipTest("Python 3.x does not support string exceptions")

def setup():
   raise "KABOOM"

def test_foo():
    assert(1==1)
