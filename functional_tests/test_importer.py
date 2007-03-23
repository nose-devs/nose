import os
import sys
import unittest
from nose.importer import Importer


class TestImporter(unittest.TestCase):

    def setUp(self):
        self.dir = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                 'support'))
        self.imp = Importer()
        self._mods = sys.modules.copy()

    def tearDown(self):
        to_del = [ m for m in sys.modules.keys() if
                   m not in self._mods ]
        if to_del:
            for mod in to_del:
                del sys.modules[mod]
        sys.modules.update(self._mods)

    def test_import_from_dir(self):
        imp = self.imp

        d1 = os.path.join(self.dir, 'dir1')
        d2 = os.path.join(self.dir, 'dir2')
        
        # simple name        
        m1 = imp.import_from_dir(d1, 'mod')
        m2 = imp.import_from_dir(d2, 'mod')
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1.__file__, m2.__file__)

        # dotted name
        p1 = imp.import_from_dir(d1, 'pak.mod')
        p2 = imp.import_from_dir(d2, 'pak.mod')
        self.assertNotEqual(p1, p2)
        self.assertNotEqual(p1.__file__, p2.__file__)

    def test_import_from_path(self):
        imp = self.imp

        jn = os.path.join
        d1 = jn(self.dir, 'dir1')
        d2 = jn(self.dir, 'dir2')
        
        # simple name        
        m1 = imp.import_from_path(jn(d1, 'mod.py'), 'mod')
        m2 = imp.import_from_path(jn(d2, 'mod.py'), 'mod')
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1.__file__, m2.__file__)

        # dotted name
        p1 = imp.import_from_path(jn(d1, 'pak', 'mod.py'), 'pak.mod')
        p2 = imp.import_from_path(jn(d2, 'pak', 'mod.py'), 'pak.mod')
        self.assertNotEqual(p1, p2)
        self.assertNotEqual(p1.__file__, p2.__file__)

        # simple name -- package
        sp1 = imp.import_from_path(jn(d1, 'pak'), 'pak')
        sp2 = imp.import_from_path(jn(d2, 'pak'), 'pak')
        self.assertNotEqual(sp1, sp2)
        assert sp1.__path__
        assert sp2.__path__
        self.assertNotEqual(sp1.__path__, sp2.__path__)

        # dotted name -- package
        dp1 = imp.import_from_path(jn(d1, 'pak', 'sub'), 'pak.sub')
        dp2 = imp.import_from_path(jn(d2, 'pak', 'sub'), 'pak.sub')
        self.assertNotEqual(dp1, dp2)
        assert dp1.__path__
        assert dp2.__path__
        self.assertNotEqual(dp1.__path__, dp2.__path__)

    def test_import_sets_intermediate_modules(self):
        imp = self.imp
        path = os.path.join(self.dir,
                            'package2', 'test_pak', 'test_sub', 'test_mod.py')
        mod = imp.import_from_path(path, 'test_pak.test_sub.test_mod')
        print mod, dir(mod)
        assert 'test_pak' in sys.modules, 'test_pak was not imported?'
        test_pak = sys.modules['test_pak']
        assert hasattr(test_pak, 'test_sub'), "test_pak.test_sub was not set"
        
    def test_cached_no_reload(self):
        imp = self.imp

        d1 = os.path.join(self.dir, 'dir1')

        # simple name
        m1 = imp.import_from_dir(d1, 'mod')
        m2 = imp.import_from_dir(d1, 'mod')        
        assert m1 is m2, "%s is not %s" % (m1, m2)

        # dotted name
        p1 = imp.import_from_dir(d1, 'pak.mod')
        p2 = imp.import_from_dir(d1, 'pak.mod')

        assert p1 is p2, "%s is not %s" % (p1, p2)
        
if __name__ == '__main__':
    unittest.main()
