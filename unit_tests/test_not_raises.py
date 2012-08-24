import unittest
import imp
import sys
from nose.tools import assert_not_raises

class TestAssertNotRaises( unittest.TestCase ):
	def test_assert_not_raises_working( self ):
		def c( x, y ):
			return x / y

		assert_not_raises( ZeroDivisionError, c, 1, 1 )

	def test_assert_not_raises_when_passed_exception_is_raised( self ):
		def c( x, y ):
			return x / y

		try:
			assert_not_raises( ZeroDivisionError, c, 1, 0 )
		except AssertionError:
			assert True

