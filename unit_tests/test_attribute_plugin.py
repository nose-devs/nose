
from nose.tools import eq_
from nose.plugins.attrib import attr

def test_flags():
    # @attr('one','two')
    def test():
        pass
    test = attr('one','two')(test)
    
    eq_(test.one, 1)
    eq_(test.two, 1)

def test_values():
    # @attr(mood="hohum", colors=['red','blue'])
    def test():
        pass
    test = attr(mood="hohum", colors=['red','blue'])(test)
    
    eq_(test.mood, "hohum")
    eq_(test.colors, ['red','blue'])

def test_mixed():
    # @attr('slow', 'net', role='integration')
    def test():
        pass
    test = attr('slow', 'net', role='integration')(test)
    
    eq_(test.slow, 1)
    eq_(test.net, 1)
    eq_(test.role, 'integration')

def test_class_attrs():
    class MyTest:
        def setUp():
            pass
        def test_one(self):
            pass
        def test_two(self):
            pass

    MyTest = attr('slow', 'net', role='integration')(MyTest)
    for n in ('test_one', 'test_two'):
        eq_(getattr(MyTest, n).slow, 1)
        eq_(getattr(MyTest, n).net, 1)
        eq_(getattr(MyTest, n).slow, 1)

    assert not hasattr(MyTest.setUp, 'slow')
    