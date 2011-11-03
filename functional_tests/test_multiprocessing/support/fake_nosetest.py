import sys

import nose

from nose.plugins.multiprocess import MultiProcess
from nose.config import Config
from nose.plugins.manager import PluginManager

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "USAGE: %s TEST_FILE" % sys.argv[0]
        sys.exit(1)
    nose.main(defaultTest=sys.argv[1], argv=[sys.argv[0],'--processes=1','-v'], config=Config(plugins=PluginManager(plugins=[MultiProcess()])))
