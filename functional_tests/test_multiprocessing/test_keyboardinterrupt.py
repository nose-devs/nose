from subprocess import Popen,PIPE
import os
import sys
from time import sleep
import signal

import nose

support = os.path.join(os.path.dirname(__file__), 'support')

PYTHONPATH = os.environ['PYTHONPATH'] if 'PYTHONPATH' in os.environ else ''
def setup():
    nose_parent_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(nose.__file__)),'..'))
    paths = [nose_parent_dir]
    if PYTHONPATH:
        paths.append(PYTHONPATH)
    os.environ['PYTHONPATH'] = os.pathsep.join(paths)
def teardown():
    if PYTHONPATH:
        os.environ['PYTHONPATH'] = PYTHONPATH
    else:
        del os.environ['PYTHONPATH']

runner = os.path.join(support, 'fake_nosetest.py')
def keyboardinterrupt(case):
    #os.setsid would create a process group so signals sent to the
    #parent process will propogates to all children processes
    from tempfile import mktemp
    logfile = mktemp()
    process = Popen([sys.executable,runner,os.path.join(support,case),logfile], preexec_fn=os.setsid, stdout=PIPE, stderr=PIPE, bufsize=-1)

    #wait until logfile is created:
    retry=100
    while not os.path.exists(logfile):
        sleep(0.1)
        retry -= 1
        if not retry:
            raise Exception('Timeout while waiting for log file to be created by fake_nosetest.py')

    os.killpg(process.pid, signal.SIGINT)
    return process, logfile

def get_log_content(logfile):
    '''prefix = 'tempfile is: '
    if not stdout.startswith(prefix):
        raise Exception('stdout does not contain tmp file name: '+stdout)
    logfile = stdout[len(prefix):].strip() #remove trailing new line char'''
    f = open(logfile)
    content = f.read()
    f.close()
    os.remove(logfile)
    return content

def test_keyboardinterrupt():
    process, logfile = keyboardinterrupt('keyboardinterrupt.py')
    stdout, stderr = [s.decode('utf-8') for s in process.communicate(None)]
    print stderr
    log = get_log_content(logfile)
    assert 'setup' in log
    assert 'test_timeout' in log
    assert 'test_timeout_finished' not in log
    assert 'test_pass' not in log
    assert 'teardown' in log
    assert 'Ran 0 tests' in stderr
    assert 'KeyboardInterrupt' in stderr
    assert 'FAILED (errors=1)' in stderr
    assert 'ERROR: Worker 0 keyboard interrupt, failing current test '+os.path.join(support,'keyboardinterrupt.py') in stderr


def test_keyboardinterrupt_twice():
    process, logfile = keyboardinterrupt('keyboardinterrupt_twice.py')
    sleep(0.5)
    os.killpg(process.pid, signal.SIGINT)
    stdout, stderr = [s.decode('utf-8') for s in process.communicate(None)]
    log = get_log_content(logfile)
    assert 'setup' in log
    assert 'test_timeout' in log
    assert 'test_timeout_finished' not in log
    assert 'test_pass' not in log
    assert 'teardown' in log
    assert 'teardown_finished' not in log
    assert 'Ran 0 tests' in stderr
    assert 'KeyboardInterrupt' in stderr
    assert 'FAILED (errors=1)' in stderr
