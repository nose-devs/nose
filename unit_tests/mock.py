from nose.case import Test
from nose.config import Config


class MockContext:
    result_proxy = None
    
    def __init__(self, parent=None, config=None):
        self.parent = parent
        if config is None:
            config = Config()
        self.config = config

    def __call__(self, test):
        return Test(self, test)

    def setup(self):
        print "Context setup called"
        if self.parent is not None:
            self.parent.setup()

    def teardown(self):
        print "Context teardown called"
        if self.parent is not None:
            self.parent.teardown()


class RecordingPluginManager(object):

    def __init__(self):
        self.reset()

    def __getattr__(self, call):
        return RecordingPluginProxy(self, call)

    def reset(self):
        self.called = {}


class RecordingPluginProxy(object):

    def __init__(self, manager, call):
        self.man = manager
        self.call = call
        
    def __call__(self, *arg, **kw):
        self.man.called.setdefault(self.call, []).append((arg, kw))
