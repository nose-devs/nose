import pickle
import sys
import unittest
import os

from nose import case
from nose.plugins import multiprocess
from nose.plugins.skip import SkipTest
from nose.config import Config
from nose.loader import TestLoader
try:
    # 2.7+
    from unittest.runner import _WritelnDecorator
except ImportError:
    from unittest import _WritelnDecorator
from warnings import warn
try:
    from multiprocessing import Manager
except ImportError:
    warn("multiprocessing module is not available, multiprocess plugin "
         "cannot be used", RuntimeWarning)


class ArgChecker:
    def __init__(self, target, args):
        self.target = target
        self.args = args
        # skip the id and queues
        pargs = args[7:]
        self.pickled = pickle.dumps(pargs)
        try:
            testQueue = args[1]
            testQueue.get(timeout=0)
        except:
            pass # ok if queue is empty
    def start(self,*args):
        pass
    def is_alive(self):
        return False

        
def setup(mod):
    multiprocess._import_mp()
    if not multiprocess.Process:
        raise SkipTest("multiprocessing not available")
    mod.Process = multiprocess.Process
    multiprocess.Process = ArgChecker
        

class T(unittest.TestCase):
    __test__ = False
    def runTest(self):
        pass

def test_mp_process_args_pickleable():
    # TODO(Kumar) this test needs to be more succint.
    # If you start seeing it timeout then perhaps we need to skip it again.
    # raise SkipTest('this currently gets stuck in poll() 90% of the time')
    test = case.Test(T('runTest'))
    config = Config()
    config.multiprocess_workers = 2
    config.multiprocess_timeout = 5
    runner = multiprocess.MultiProcessTestRunner(
        stream=_WritelnDecorator(sys.stdout),
        verbosity=10,
        loaderClass=TestLoader,
        config=config)
    runner.run(test)
        

def add_pid_callback(pid_list):
    pid_list.append(os.getpid())


def check_pid_callback(pid_list):
    assert len(pid_list) > 0
    assert os.getpid() in pid_list


def del_pid_callback(pid_list):
    pid_list.remove(os.getpid())


def test_mp_process_callbacks_register_first():
    """Register callbacks first and then create Config. The startup callback
    adds the PID on a shared list, and the stop callbacks respectively
    check if the PID is there and then delete it."""

    manager = Manager()
    pid_list = manager.list()

    opts = type('options', (object,), {'multiprocess_workers': 2,
                                       'multiprocess_timeout': 5,
                                       'multiprocess_restartworker': False})
    mp_plugin = multiprocess.MultiProcess()
    mp_plugin.register_start_callback(add_pid_callback, pid_list)
    # We add a second one, so that we can check at the end that len(list) == 2
    mp_plugin.register_start_callback(add_pid_callback, pid_list)
    mp_plugin.register_stop_callback(check_pid_callback, pid_list)
    mp_plugin.register_stop_callback(del_pid_callback, pid_list)
    mp_plugin.configure(opts, Config())

    test = case.Test(T('runTest'))
    runner = multiprocess.MultiProcessTestRunner(
                stream=_WritelnDecorator(sys.stdout),
                verbosity=10,
                loaderClass=TestLoader,
                config=mp_plugin.config)
    runner.run(test)

    assert len(pid_list) == 2


def test_mp_process_callbacks_config_first():
    """Create Config first and then register callbacks. The startup callback
    adds the PID on a shared list, and the stop callbacks respectively
    check if the PID is there and then delete it."""

    manager = Manager()
    pid_list = manager.list()

    opts = type('options', (object,), {'multiprocess_workers': 2,
                                       'multiprocess_timeout': 5,
                                       'multiprocess_restartworker': False})
    mp_plugin = multiprocess.MultiProcess()
    mp_plugin.configure(opts, Config())
    mp_plugin.register_start_callback(add_pid_callback, pid_list)
    # We add a second one, so that we can check at the end that len(list) == 2
    mp_plugin.register_start_callback(add_pid_callback, pid_list)
    mp_plugin.register_stop_callback(check_pid_callback, pid_list)
    mp_plugin.register_stop_callback(del_pid_callback, pid_list)

    test = case.Test(T('runTest'))
    runner = multiprocess.MultiProcessTestRunner(
                stream=_WritelnDecorator(sys.stdout),
                verbosity=10,
                loaderClass=TestLoader,
                config=mp_plugin.config)
    runner.run(test)

    assert len(pid_list) == 2

