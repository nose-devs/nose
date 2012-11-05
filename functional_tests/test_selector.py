import os
import unittest
from nose.selector import TestAddress

support = os.path.abspath(os.path.join(os.path.dirname(__file__), 'support'))

class TestTestAddress(unittest.TestCase):

    def test_module_filename(self):
        wd = os.path.join(support, 'package2')
        addr = TestAddress('test_pak.test_mod', workingDir=wd)
        self.assertEqual(addr.filename,
                         os.path.join(wd, 'test_pak', 'test_mod.py'))

    def test_test_verbose_name_function(self):
        wd = os.path.join(support, 'package2')
        addr = TestAddress('test_pak.test_mod.test_add', workingDir=wd)
        self.assertEqual(addr.filename,
                         os.path.join(wd, 'test_pak', 'test_mod.py'))
        self.assertEqual(addr.call, 'test_add')

    def test_test_verbose_name_method(self):
        wd = os.path.join(support, 'att')
        addr = TestAddress('test_attr.TestClass.test_class_one', workingDir=wd)
        self.assertEqual(addr.filename, os.path.join(wd, 'test_attr.py'))
        self.assertEqual(addr.call, 'TestClass.test_class_one')


if __name__ == '__main__':
    unittest.main()
