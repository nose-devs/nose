from test_pak import state

def setup():
    state.append('test_pak.test_sub.setup')

def teardown():
    state.append('test_pak.test_sub.teardown')
