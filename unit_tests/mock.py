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
