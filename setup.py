import sys
import os

VERSION = '0.11.4'
py_vers_tag = '-%s.%s' % sys.version_info[:2]

test_dirs = ['functional_tests', 'unit_tests', os.path.join('doc','doc_tests')]

try:
    from setuptools import setup, find_packages
    addl_args = dict(
        zip_safe = False,
        packages = find_packages(),
        entry_points = {
        'console_scripts': [
            'nosetests = nose:run_exit',
            'nosetests%s = nose:run_exit' % py_vers_tag,
            ],
        'distutils.commands': [
            ' nosetests = nose.commands:nosetests',
            ],
        },
        test_suite = 'nose.collector',
        )

    # This is required by multiprocess plugin; on Windows, if
    # the launch script is not import-safe, spawned processes
    # will re-run it, resulting in an infinite loop.
    if sys.platform == 'win32':
        import re
        from setuptools.command.easy_install import easy_install

        def wrap_write_script(self, script_name, contents, *arg, **kwarg):
            bad_text = re.compile(
                "\n"
                "sys.exit\(\n"
                "   load_entry_point\(([^\)]+)\)\(\)\n"
                "\)\n")
            good_text = (
                "\n"
                "if __name__ == '__main__':\n"
                "    sys.exit(\n"
                r"        load_entry_point(\1)()\n"
                "    )\n"
                )
            contents = bad_text.sub(good_text, contents)
            return self._write_script(script_name, contents, *arg, **kwarg)
        easy_install._write_script = easy_install.write_script
        easy_install.write_script = wrap_write_script

except ImportError:
    from distutils.core import setup
    addl_args = dict(
        packages = ['nose', 'nose.ext', 'nose.plugins'],
        scripts = ['bin/nosetests'],
        )

if sys.version_info >= (3,):
    from distutils.core import Command
    from distutils.util import Mixin2to3
    from distutils import dir_util, file_util, log
    #from distutils.command import build
    import setuptools.command.test
    from pkg_resources import normalize_path

    class BuildTestsCommand (Command, Mixin2to3):
        # Create mirror copy of tests, convert all .py files using 2to3
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            bcmd = self.get_finalized_command('build')
            self.build_base = bcmd.build_base
            self.test_base = os.path.join(self.build_base, 'tests')

        def run(self):
            #self.run_command('egg_info')
            build_base = self.build_base
            test_base = self.test_base
            bpy_cmd = self.get_finalized_command("build_py")
            lib_base = normalize_path(bpy_cmd.build_lib)
            modified = []
            py_modified = []
            for testdir in test_dirs:
              for srcdir, dirnames, filenames in os.walk(testdir):
                destdir = os.path.join(test_base, srcdir)
                dir_util.mkpath(destdir)
                for fn in filenames:
                    if fn.startswith("."):
                        continue # skip .svn folders and such
                    dstfile, copied = file_util.copy_file(
                                          os.path.join(srcdir, fn),
                                          os.path.join(destdir, fn),
                                          update=True)
                    if copied:
                        modified.append(dstfile)
                        if fn.endswith('.py'):
                            py_modified.append(dstfile)
            self.run_2to3(py_modified)

            file_util.copy_file('setup.cfg', build_base, update=True)
            dir_util.mkpath(lib_base)
            self.reinitialize_command('egg_info', egg_base=lib_base)
            self.run_command('egg_info')

    class TestCommand (setuptools.command.test.test):
        # Override 'test' command to make sure 'build_tests' gets run first.
        def run(self):
            self.run_command('build_tests')
            setuptools.command.test.test.run(self)

    #class build_py3(build.build):
    #    # Override 'build' command for Python 3 to trigger 'build_tests' too
    #    def build_tests(self):
    #        return sys.version_info >= (3,0)
    #    sub_commands = build.build.sub_commands + [('build_tests', build_tests)]

    addl_args['use_2to3'] = True
    addl_args['cmdclass'] = dict(
        build_tests = BuildTestsCommand,
        test = TestCommand,
        #build = build_py3,
    )

setup(
    name = 'nose',
    version = VERSION,
    author = 'Jason Pellerin',
    author_email = 'jpellerin+nose@gmail.com',
    description = ('nose extends unittest to make testing easier'),
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
    found on in the nose API documentation, here:
    http://somethingaboutorange.com/mrl/projects/nose/

    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the unstable development version instead:
    http://bitbucket.org/jpellerin/nose/get/tip.gz#egg=nose-dev
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

