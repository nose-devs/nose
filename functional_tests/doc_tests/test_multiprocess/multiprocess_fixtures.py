import sys
import subprocess
import os
from nose.plugins.skip import SkipTest
from nose.plugins.plugintest import munge_nose_output_for_doctest

_multiprocess_can_split_ = True

def setup_module():
    try:
        import multiprocessing
        # FIXME if mp plugin is enabled, skip
    except ImportError:
        try:
            import processing
        except ImportError:
            raise SkipTest("processing module not available")


def globs(globs):
    globs.update({'sh': sh})
    return globs


def sh(cmd):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))))            
    cmd = cmd.replace('nosetests ', '')
    output = subprocess.Popen(
        [executable(), 'selftest.py'] + cmd.split(' '),
        cwd=root, stderr=subprocess.PIPE, close_fds=True).communicate()[1]
    print munge_nose_output_for_doctest(output)

    
def executable():
    return sys.executable
