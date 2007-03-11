"""Implements an importer that looks only in specific path (ignoring
sys.path), and uses a per-path cache in addition to sys.modules. This is
necessary because test modules in different directories frequently have the
same names, which means that the first loaded would mask the rest when using
the builtin importer.
"""

# FIXME use imputil? This is almost exactly _FileSystemImport.import_from_dir

import imputil
import logging
import os
import sys
from nose.config import Config

#from imp import find_module, load_module, acquire_lock, release_lock, \
#     load_source as _load_source

log = logging.getLogger(__name__)
#_modules = {}

class Importer(object):
    
    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.config = config
        if not imputil._os_stat:
            imputil._os_bootstrap()
        self._imp = imputil._FilesystemImporter()
        self._imp.add_suffix('.py', imputil.py_suffix_importer)
        self._modules = {}

    def import_from_path(self, path, fqname):
        finfo = os.stat(path)
        # ensure that the parent path is on sys.path
        if self.config.addPaths:
            add_path(os.path.dirname(path))
        result = imputil.py_suffix_importer(path, finfo, fqname)
        if result:
            return self._imp._process_result(result, fqname)
        raise ImportError("Unable to import %s from %s" % (fqname, path))
        
    def import_from_dir(self, dir, fqname):
        dir = os.path.abspath(dir)
        cache = self._modules.setdefault(dir, {})
        if fqname in cache:
            # print "Returning cached %s:%s" % (dir, fqname)
            return cache[fqname]
        parts = fqname.split('.')
        loaded = []
        for part in parts:
            # print "load %s from %s" % (part, dir)
            loaded.append(part)
            part_fqname = '.'.join(loaded)
            # FIXME push dir onto sys.path
            mod = self._imp.import_from_dir(dir, part)
            cache[part_fqname] = mod
            dir = os.path.join(dir, part)
        return mod
        
def add_path(path):
    """Ensure that the path, or the root of the current package (if
    path is in a package) is in sys.path.
    """

    # FIXME add any src-looking dirs seen too... need to get config for that
    
    log.debug('Add path %s' % path)    
    if not path:
        return []
    added = []
    parent = os.path.dirname(path)
    if (parent
        and os.path.exists(os.path.join(path, '__init__.py'))):
        added.extend(add_path(parent))
    elif not path in sys.path:
        log.debug("insert %s into sys.path", path)
        sys.path.insert(0, path)
        added.append(path)
    return added

def remove_path(path):
    log.debug('Remove path %s' % path)
    if path in sys.path:
        sys.path.remove(path)


# def load_source(name, path, conf):
#     """Wrap load_source to make sure that the dir of the module (or package)
#     is in sys.path before the module is loaded.
#     """
#     if conf.addPaths:
#         add_path(os.path.dirname(path))
#     return _load_source(name, path)
                 
# def _import(name, path, conf):
#     """Import a module *only* from path, ignoring sys.path and
#     reloading if the version in sys.modules is not the one we want.
#     """
#     log.debug("Import %s from %s (addpaths: %s)", name, path, conf.addPaths)
    
#     # special case for __main__
#     if name == '__main__':
#         return sys.modules[name]

#     # make sure we're doing an absolute import
#     # name, path = make_absolute(name, path)
    
#     if conf.addPaths:
#         for p in path:
#             if p is not None:
#                 add_path(p)

#     path = [ p for p in path if p is not None ]
#     cache = _modules.setdefault(':'.join(path), {})

#     # quick exit for fully cached names
#     if cache.has_key(name):
#         return cache[name]
    
#     parts = name.split('.')
#     fqname = ''
#     mod = parent = fh = None
    
#     for part in parts:
#         if fqname == '':
#             fqname = part
#         else:
#             fqname = "%s.%s" % (fqname, part)

#         if cache.has_key(fqname):
#             mod = cache[fqname]
#         else:
#             try:
#                 acquire_lock()
#                 log.debug("find module part %s (%s) at %s", part, fqname, path)
#                 fh, filename, desc = find_module(part, path)
#                 old = sys.modules.get(fqname)
#                 if old:
#                     # test modules frequently have name overlap; make sure
#                     # we get a fresh copy of anything we are trying to load
#                     # from a new path
#                     if hasattr(old,'__path__'):
#                         old_path = os.path.normpath(old.__path__[0])
#                         old_ext = None
#                     elif hasattr(old, '__file__'):
#                         old_norm = os.path.normpath(old.__file__)
#                         old_path, old_ext = os.path.splitext(old_norm)
#                     else:
#                         # builtin or other module-like object that
#                         # doesn't have __file__
#                         old_path, old_ext, old_norm = None, None, None
#                     new_norm = os.path.normpath(filename)
#                     new_path, new_ext = os.path.splitext(new_norm)
#                     if old_path == new_path:
#                         log.debug("module %s already loaded "
#                                   "old: %s %s new: %s %s", fqname, old_path,
#                                   old_ext, new_path, new_ext)
#                         cache[fqname] = mod = old
#                         continue
#                     else:
#                         del sys.modules[fqname]
#                 log.debug("Loading %s from %s", fqname, filename)
#                 mod = load_module(fqname, fh, filename, desc)
#                 log.debug("%s from %s yields %s", fqname, filename, mod)
#                 cache[fqname] = mod
#             finally:
#                 if fh:
#                     fh.close()
#                 release_lock()
#         if parent:
#             setattr(parent, part, mod)
#         if hasattr(mod, '__path__'):
#             path = mod.__path__
#         parent = mod
#     return mod

def make_absolute(name, path):
    """Given a module name and the path at which it is found, back up to find
    the parent of the module, popping directories off of the path so long as
    they contain __init__.py files.
    """
    if not os.path.exists(os.path.join(path, '__init__.py')):
        return (name, path)
    path, parent = os.path.split(path)
    name = "%s.%s" % (parent, path)
    return make_absolute(name, path)
