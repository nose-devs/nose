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

        # simple name
        d1 = os.path.join(self.dir, 'dir1')
        m1 = imp.import_from_dir(d1, 'mod')
        d2 = os.path.join(self.dir, 'dir2')
        m2 = imp.import_from_dir(d2, 'mod')
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1.__file__, m2.__file__)

        # dotted name
        p1 = imp.import_from_dir(d1, 'pack.mod')
        p2 = imp.import_from_dir(d2, 'pack.mod')
        self.assertNotEqual(p1, p2)
        self.assertNotEqual(p1.__file__, p2.__file__)
        


if __name__ == '__main__':
    unittest.main()
