"""
This module contains fixups for using nose under different versions of Python.
"""
import sys
import os
import types
import inspect
import nose.util

__all__ = ['make_instancemethod', 'cmp', 'sort_list', 'ClassType', 'TypeType', 'UNICODE_STRINGS', 'unbound_method', 'ismethod', 'isunboundmethod']

# In Python 3.x, all strings are unicode (the call to 'unicode()' in the 2.x
# source will be replaced with 'str()' when running 2to3, so this test will
# then become true)
UNICODE_STRINGS = (type(unicode()) == type(str()))

# new.instancemethod() is obsolete for new-style classes (Python 3.x)
# We need to use descriptor functions instead.
try:
    import new
    def make_instancemethod(function, instance):
        return new.instancemethod(function.im_func, instance, instance.__class__)
except ImportError:
    def make_instancemethod(function, instance):
        return function.__get__(instance, instance.__class__)

# Python 3.x has gotten rid of the 'cmp' option to list.sort (and the 'cmp'
# builtin).
# Unfortunately, using a 'key' argument isn't supported in Python 2.3, which
# we're still trying to support too...
if hasattr(__builtins__, 'cmp'):
    def sort_list(l, cmp):
        return l.sort(cmp)
else:
    def cmp(a, b):
        return (a > b) - (a < b)

    def cmp_to_key(mycmp):
        class K(object):
            def __init__(self, obj, *args):
                self.obj = obj
            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0
            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0
            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0
            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0
            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0
            def __ne__(self, other):
                return mycmp(self.obj, other.obj) != 0
        return K

    def sort_list(l, cmp):
        return l.sort(key=cmp_to_key(cmp))

# In Python 3.x, all objects are "new style" objects descended from 'type', and
# thus types.ClassType and types.TypeType doen't exist anymore.  For
# compatibility, we make sure they still work.
if hasattr(types, 'ClassType'):
    ClassType = types.ClassType
    TypeType = types.TypeType
else:
    ClassType = type
    TypeType = type

# The following emulates the behavior (we need) of an 'unbound method' under
# Python 3.x (namely, the ability to have a class associated with a function
# definition so that things can do stuff based on its associated class)
class UnboundMethod:
    def __init__(self, cls, func):
        self.func = func
        self.__self__ = UnboundSelf(cls)

    def address(self):
        cls = self.__self__.cls
        module = cls.__module__
        m = sys.modules[module]
        file = getattr(m, '__file__', None)
        if file is not None:
            file = os.path.abspath(file)
        return (nose.util.src(file), module, "%s.%s" % (cls.__name__, self.func.__name__))

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self.func, attr)

class UnboundSelf:
    def __init__(self, cls):
        self.cls = cls

    # We have to do this hackery because Python won't let us override the
    # __class__ attribute...
    def __getattribute__(self, attr):
        if attr == '__class__':
            return self.cls
        else:
            return object.__getattribute__(self, attr)

def unbound_method(cls, func):
    if inspect.ismethod(func):
        return func
    if not inspect.isfunction(func):
        raise TypeError('%s is not a function' % (repr(func),))
    return UnboundMethod(cls, func)

def ismethod(obj):
    return inspect.ismethod(obj) or isinstance(obj, UnboundMethod)

def isunboundmethod(obj):
    return (inspect.ismethod(obj) and obj.im_self is None) or isinstance(obj, UnboundMethod)
