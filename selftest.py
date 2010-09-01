#!/usr/bin/env python

"""Test the copy of nose in this directory, by running that nose against itself.

You can test nose using nose in other ways, but if you don't use this script,
you might have one installation of nose testing another installation, which is
not supported.
"""

# More detail:

# In the absence of some sort of deep renaming magic, nose can't reasonably
# test a different installation of itself, given the existence of the global
# module registry sys.modules .

# If installed system-wide with setuptools, setuptools (via the site-packages
# easy-install.pth) takes you at your word and ensures that the installed nose
# comes first on sys.path .  So the only way to test a copy of nose other than
# the installed one is to install that version (e.g. by running python setup.py
# develop).

# This script provides a way of running nose on nose's own tests without
# installing the version to be tested, nor uninstalling the currently-installed
# version.

import os
import sys


if __name__ == "__main__":
    this_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
    if sys.version_info >= (3,):
	# Under Python 3.x, we need to 'build' the source (using 2to3, etc)
	# first, so it will be located under build/lib/nose instead of this
	# dir.
        this_dir = os.path.join(this_dir, 'build', 'lib')
    try:
        import pkg_resources
        env = pkg_resources.Environment(search_path=[this_dir])
        distributions = env["nose"]
        assert len(distributions) == 1
        dist = distributions[0]
        dist.activate()
    except ImportError:
        pass
    # Always make sure our chosen version is first on the path
    sys.path.insert(0, this_dir)
    os.chdir(this_dir)
    import nose
    nose.run_exit()
