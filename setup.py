import sys
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from nose import __version__ as VERSION

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
                        'nose is highly adaptable and customizable through '
                        'the use of plugins. More information about writing '
                        'plugins may be found on the wiki, here: '
                        'http://code.google.com/p/python-nose/wiki/'
                        'WritingPlugins.\n\n'
                        'If you have recently reported a bug marked as fixed, '
                        'or have a craving for the very latest, you may want '
                        'the development version instead: '
                        'http://python-nose.googlecode.com/svn/trunk'
                        '#egg=nose-dev'
                        ),
    license = 'GNU LGPL',
    keywords = 'test unittest doctest automatic discovery',
    url = 'http://somethingaboutorange.com/mrl/projects/nose/',
    download_url = \
    'http://somethingaboutorange.com/mrl/projects/nose/nose-%s.tar.gz' \
    % VERSION,
    package_data = { '': [ '*.txt' ] },
    packages = find_packages(),
    entry_points = {        
        'console_scripts': [
            'nosetests = nose:run_exit'
            ],
        'nose.plugins': [
            'coverage = nose.plugins.cover:Coverage',
            'doctest = nose.plugins.doctests:Doctest',
            'profile = nose.plugins.prof:Profile',
            'attrib = nose.plugins.attrib:AttributeSelector',
            'missed = nose.plugins.missed:MissedTests',
            'isolation = nose.plugins.isolate:IsolationPlugin'
            ],
        'distutils.commands': [
            ' nosetests = nose.commands:nosetests'
            ],
        },
    test_suite = 'nose.collector',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
        ]
    )
