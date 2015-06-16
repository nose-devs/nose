import multiprocessing

manager = multiprocessing.Manager()
lock = manager.Lock()
dict_ = manager.dict()


def test_multiprocessing():
    "Test that the import machinery doesn't get locked by the manager"
    pass
