"""Useful mock objects.
"""

class Bucket(object):
    def __init__(self, **kw):
        self.__dict__['d'] = {}
        self.__dict__['d'].update(kw)
        
    def __getattr__(self, attr):
        if not self.__dict__.has_key('d'):
            return None
        return self.__dict__['d'].get(attr)

    def __setattr__(self, attr, val):        
        self.d[attr] = val


class MockOptParser(object):
    def __init__(self):
        self.opts = []
    def add_option(self, *args, **kw):
        self.opts.append((args, kw))

        
class Mod(object):
    def __init__(self, name, **kw):
        self.__name__ = name
        if 'file' in kw:
            self.__file__ = kw.pop('file')
        else:
            if 'path' in kw:
                path = kw.pop('path')
            else:
                path = ''        
            self.__file__ = "%s/%s.pyc" % (path, name.replace('.', '/'))
        self.__path__ = [ self.__file__ ] # FIXME?
        self.__dict__.update(kw)


class Result(object):
    def __init__(self):
        from nose.result import Result
        import types
        self.errors = []
        for attr in dir(Result):
            if type(getattr(Result, attr)) is types.MethodType:
                if not hasattr(self, attr):
                    setattr(self, attr, lambda s, *a, **kw: None)
            elif not attr.startswith('__'):
                setattr(self, attr, None)

    def addError(self, test, err):
        self.errors.append(err)
