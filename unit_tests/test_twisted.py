from nose.tools import *
from nose.twistedtools import *

from twisted.internet.defer import Deferred
from twisted.internet.error import DNSLookupError

class CustomError(Exception):
    pass

# Should succeed unless python-hosting is down
@deferred()
def test_resolve():
    return reactor.resolve("nose.python-hosting.com")

# Raises TypeError because the function does not return a Deferred
@raises(TypeError)
@deferred()
def test_raises_bad_return():
    reactor.resolve("nose.python-hosting.com")

# Check we propagate twisted Failures as Exceptions
# (XXX this test might take some time: find something better?)
@raises(DNSLookupError)
@deferred()
def test_raises_twisted_error():
    return reactor.resolve("x.y.z")

# Check we detect Exceptions inside the callback chain
@raises(CustomError)
@deferred(timeout=1.0)
def test_raises_callback_error():
    d = Deferred()
    def raise_error(_):
        raise CustomError()
    def finish():
        d.callback(None)
    d.addCallback(raise_error)
    reactor.callLater(0.01, finish)
    return d

# Check we detect Exceptions inside the test body
@raises(CustomError)
@deferred(timeout=1.0)
def test_raises_plain_error():
    raise CustomError

# The deferred is triggered before the timeout: ok
@deferred(timeout=1.0)
def test_timeout_ok():
    d = Deferred()
    def finish():
        d.callback(None)
    reactor.callLater(0.01, finish)
    return d

# The deferred is triggered after the timeout: failure
@raises(TimeExpired)
@deferred(timeout=0.1)
def test_timeout_expired():
    d = Deferred()
    def finish():
        d.callback(None)
    reactor.callLater(1.0, finish)
    return d

