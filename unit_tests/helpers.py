def iter_compat(suite):
    try:
        suite.__iter__
        return suite
    except AttributeError:
        return suite._tests


from nose.config import Config
import weakref
try:
    import copy_reg
except ImportError:
    import copyreg as copy_reg


class SelfReferencePickleConfig(Config):
    
    instance_refs = {}
    
    def __init__(self, *args, **kwargs):
        
        super(SelfReferencePickleConfig, self).__init__(*args, **kwargs)
        self.multiprocess_timeout = 1
        self.multiprocess_restartworker = False
        SelfReferencePickleConfig.instance_refs[id(self)] = weakref.ref(self)
    
    def __getstate__(self):
        
        return False


def _pickle_srpc(srpc):
    
    return _unpickle_srpc, (id(srpc),)

def _unpickle_srpc(srpc_id):
    
    try:
        inst = SelfReferencePickleConfig.instance_refs[srpc_id]()
    except KeyError:
        pass
    else:
        if inst is None:
            del SelfReferencePickleConfig.instance_refs[srpc_id]
        else:
            return inst
    raise ValueError('Tried to unpickle SelfReferencePickleConfig instance '
                     'that never existed or has been destroyed.')

copy_reg.pickle(SelfReferencePickleConfig, _pickle_srpc, _unpickle_srpc)