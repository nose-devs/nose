
from nose.tools import eq_
from nose.plugins.attrib import attr

def test_flags():
    @attr('one','two')
    def test():
        pass
    
    eq_(test.one, 1)
    eq_(test.two, 1)

def test_values():
    @attr(mood="hohum", colors=['red','blue'])
    def test():
        pass
    
    eq_(test.mood, "hohum")
    eq_(test.colors, ['red','blue'])

def test_mixed():
    @attr('slow', 'net', role='integration')
    def test():
        pass
    
    eq_(test.slow, 1)
    eq_(test.net, 1)
    eq_(test.role, 'integration')
    