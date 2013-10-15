"""Loop mode plugin.

Simple plugging to signal that we want to run tests in a loop.

    $ nosetets --with-loop
    # TEST LOOP HERE... press Ctrl+C to exit.

The ``NOSE['status']`` shared variable is used to signal the state/mode in
which nose is running. It can have one of the following values:

* `normal` - regular business, not looping
* `looping` - run in the loop
* `exiting` - final run of teardown when exiting the loop.


.. code-block:: python

    from nose.core import NOSE

    selenium_process = None

    def setup_package():
        global selenium_process

        # Don't start selenium if it is already started.
        if selenium_process:
            return

        selenium_path = os.path.join(
            selenium_standalone.MODULE_PATH,
            'selenium-server-standalone.jar',
            )
        command = ['java', '-jar', selenium_path]
        with open(os.devnull, 'w') as devnull:
            selenium_process = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                stdout=devnull,
                )

    def teardown_package():
        # Don't close selenium when looping tests.
        if NOSE['state'] == 'looping':
            return

        os.kill(selenium_process.pid, signal.SIGKILL)
"""
from nose.plugins.base import Plugin


class LoopPlugin(Plugin):
    """
    Simple loop plugin.
    """
    name = 'loop'
