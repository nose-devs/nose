import maths
from test_pak import state

def setup():
    state.append('test_mod.setup')

def test_add():
    state.append('test_mod.test_add')
    assert maths.add(1, 2) == 3

def teardown():
    state.append('test_mod.teardown')
