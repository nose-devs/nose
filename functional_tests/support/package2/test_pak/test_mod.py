import maths
from test_pak import state

def setup():
    state.append('test_pak.test_mod.setup')

def test_add():
    state.append('test_pak.test_mod.test_add')
    assert maths.add(1, 2) == 3

def test_minus():
    state.append('test_pak.test_mod.test_minus')
    
def teardown():
    state.append('test_pak.test_mod.teardown')
