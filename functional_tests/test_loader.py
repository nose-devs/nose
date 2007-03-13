import os
import sys
import unittest
from nose import loader

support = os.path.join(os.path.dirname(__file__), 'support')

class TestNoseTestLoader(unittest.TestCase):

    def setUp(self):
        self._mods = sys.modules.copy()

    def tearDown(self):
        to_del = [ m for m in sys.modules.keys() if
                   m not in self._mods ]
        if to_del:
            for mod in to_del:
                del sys.modules[mod]
        sys.modules.update(self._mods)

    def test_load_from_name_file(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package1')
        l = loader.TestLoader(working_dir=wd)

        file_suite = l.loadTestsFromName('tests/test_example_function.py')
        for t in file_suite:
            print t
            t(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

    def test_load_from_name_dot(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package1')
        l = loader.TestLoader(working_dir=wd)
        dir_suite = l.loadTestsFromName('.')
        for t in dir_suite:
            print "dir ", t
            t(res)
        assert not res.errors, res.errors
        assert not res.failures, res.failures

    def test_fixture_context(self):
        res = unittest.TestResult()
        wd = os.path.join(support, 'package2')
        l = loader.TestLoader(working_dir=wd)
        dir_suite = l.loadTestsFromName('.')
        dir_suite(res)

        m = sys.modules['test_pak']
        print "test pak state", m.state

        assert not res.errors, res.errors
        assert not res.failures, res.failures
        self.assertEqual(res.testsRun, 5)

        # Expected order of calls
        expect = ['test_pak.setup',
                  'test_pak.test_mod.setup',
                  'test_pak.test_mod.test_add',
                  'test_pak.test_mod.test_minus',
                  'test_pak.test_mod.teardown',
                  'test_pak.test_sub.setup',
                  'test_pak.test_sub.test_mod.setup',
                  'test_pack.test_sub.test_mod.TestMaths.setup_class',
                  'test_pack.test_sub.test_mod.TestMaths.setup',
                  'test_pack.test_sub.test_mod.TestMaths.test_div',
                  'test_pack.test_sub.test_mod.TestMaths.teardown',
                  'test_pack.test_sub.test_mod.TestMaths.setup',
                  'test_pack.test_sub.test_mod.TestMaths.test_two_two',
                  'test_pack.test_sub.test_mod.TestMaths.teardown',
                  'test_pack.test_sub.test_mod.TestMaths.teardown_class',
                  'test_pak.test_sub.test_mod.test',
                  'test_pak.test_sub.test_mod.teardown',
                  'test_pak.test_sub.teardown',
                  'test_pak.teardown']
        self.assertEqual(len(m.state), len(expect))
        for item in m.state:
            self.assertEqual(item, expect.pop(0))
            
        
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
