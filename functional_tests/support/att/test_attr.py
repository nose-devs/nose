import unittest

def test_one():
    pass
test_one.a = 1

def test_two():
    pass
test_two.a = 1

def test_three():
    pass
test_three.b = 1

class TestClass:
    a = 1
    def test_class_one(self):
        pass

    def test_class_two(self):
        pass
    test_class_two.b = 2

    def test_class_three(self):
        pass

    
class Something(unittest.TestCase):
    b = 2
    def test_case_one(self):
        pass
    
    def test_case_two(self):
        pass
    
    def test_case_three(self):
        pass
