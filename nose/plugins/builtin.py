"""
Lists builtin plugins
"""

from nose.plugins.attrib import AttributeSelector
from nose.plugins.cover import Coverage
from nose.plugins.doctests import Doctest
## from nose.plugins.isolation import 
from nose.plugins.prof import Profile

plugins = [AttributeSelector, Coverage, Doctest, Profile]
