import sys
from nose import __version__ as VERSION

try:
    from setuptools import setup, find_packages
    addl_args = dict(
        packages = find_packages(),
        entry_points = {        
        'console_scripts': [
            'nosetests = nose:run_exit'
            ],
        'distutils.commands': [
            ' nosetests = nose.commands:nosetests'
            ],
        },
        test_suite = 'nose.collector',
        )
except ImportError:
    addl_args = dict(
        packages = 'FIXME',
        # FIXME -- nosetests script
        )
    
setup(
    name = 'nose',
    version = VERSION,
    author = 'Jason Pellerin',
    author_email = 'jpellerin+nose@gmail.com',
    description = ('A unittest extension offering automatic test suite '
                   'discovery, simplified test authoring, and output capture'),
    long_description = ('nose provides an alternate test discovery and '
                        'running process for unittest, one that is intended '
                        'to mimic the behavior of py.test as much as is '
                        'reasonably possible without resorting to magic. '
                        'By default, nose will run tests in files or '
                        'directories under the current working directory '
                        'whose names include "test". nose also supports '
                        'doctest tests and may optionally provide a '
                        'test coverage report.\n\n'
                        'If you have recently reported a bug marked as fixed, '
                        'or have a craving for the very latest, you may want '
                        'the development version instead: '
                        'http://svn.nose.python-hosting.com/trunk#egg=nose-dev'
                        ),
    license = 'GNU LGPL',
    keywords = 'test unittest doctest automatic discovery',
    url = 'http://somethingaboutorange.com/mrl/projects/nose/',
    download_url = \
    'http://somethingaboutorange.com/mrl/projects/nose/nose-%s.tar.gz' \
    % VERSION,
    package_data = { '': [ '*.txt' ] },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
        ],
    **addl_args
    )
