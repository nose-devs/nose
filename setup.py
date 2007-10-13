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
    from distutils.core import setup
    addl_args = dict(
        packages = ['nose', 'nose.ext', 'nose.plugins'],
        scripts = ['bin/nosetests']
        )
    
setup(
    name = 'nose',
    version = VERSION,
    author = 'Jason Pellerin',
    author_email = 'jpellerin+nose@gmail.com',
    description = ('A unittest extension offering automatic test suite '
                   'discovery and easy test authoring'),
    long_description = \
    """nose extends the test loading and running features of unittest, making
    it easier to write, find and run tests.

    By default, nose will run tests in files or directories under the current
    working directory whose names include "test" or "Test" at a word boundary
    (like "test_this" or "functional_test" or "TestClass" but not
    "libtest"). Test output is similar to that of unittest, but also includes
    captured stdout output from failing tests, for easy print-style debugging.
                        
    These features, and many more, are customizable through the use of
    plugins. Plugins included with nose provide support for doctest, code
    coverage and profiling, flexible attribute-based test selection,
    output capture and more. More information about writing plugins may be 
    found on the wiki, here:
    http://code.google.com/p/python-nose/wiki/WritingPlugins, and in the nose
    API documentation, here:
    http://somethingaboutorange.com/mrl/projects/nose/doc/
    
    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the development version instead:
    http://python-nose.googlecode.com/svn/trunk#egg=nose-dev
    """,
    license = 'GNU LGPL',
    keywords = 'test unittest doctest automatic discovery',
    url = 'http://somethingaboutorange.com/mrl/projects/nose/',
    download_url = \
    'http://somethingaboutorange.com/mrl/projects/nose/nose-%s.tar.gz' \
    % VERSION,
    data_files = [('man/man1', ['nosetests.1'])],
    package_data = {'': ['*.txt',
                         'examples/*.py',
                         'examples/*/*.py']},
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
        ],
    **addl_args
    )
