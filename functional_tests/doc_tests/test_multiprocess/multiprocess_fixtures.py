import sys
import os
from nose.plugins.skip import SkipTest
from nose.plugins.multiprocess import MultiProcess
from nose.plugins.plugintest import munge_nose_output_for_doctest

_multiprocess_can_split_ = True

def setup_module():
    try:
        import multiprocessing
        if 'active' in MultiProcess.status:
            raise SkipTest("Multiprocess plugin is active. Skipping tests of "
                           "plugin itself. multiprocessing module in python "
                           "2.6 is not re-entrant")
    except ImportError:
        try:
            import processing
        except ImportError:
            raise SkipTest("processing module not available")
    try:
        import subprocess
    except ImportError:
        raise SkipTest("subprocess module not available")



def globs(globs):
    globs.update({'sh': sh})
    return globs


def sh(cmd):
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))))            
    cmd = cmd.replace('nosetests ', '')
    output = subprocess.Popen(
        [executable(), 'selftest.py'] + cmd.split(' '),
        cwd=root, stderr=subprocess.PIPE, close_fds=True).communicate()[1]
    print munge_nose_output_for_doctest(output)

    
def executable():
    return sys.executable
