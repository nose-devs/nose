"""Implements an importer that looks only in specific path (ignoring
sys.path), and uses a per-path cache in addition to sys.modules. This is
necessary because test modules in different directories frequently have the
same names, which means that the first loaded would mask the rest when using
the builtin importer.
"""
from __future__ import generators

import logging
import os
import sys
from imp import find_module, load_module, acquire_lock, release_lock

log = logging.getLogger(__name__)
_modules = {}


def add_path(path):
    """Ensure that the path, or the root of the current package (if
    path is in a package) is in sys.path.
    """
    log.debug('Add path %s' % path)
    if not path:
        return
    parent = os.path.dirname(path)
    if (parent
        and os.path.exists(os.path.join(path, '__init__.py'))):
        add_path(parent)
    elif not path in sys.path:
        log.debug("insert %s into sys.path", path)
        sys.path.insert(0, path)

        
def _import(name, path, conf):
    """Import a module *only* from path, ignoring sys.path and
    reloading if the version in sys.modules is not the one we want.
    """
    log.debug("Import %s from %s (addpaths: %s)", name, path, conf.addPaths)
    
    # special case for __main__
    if name == '__main__':
        return sys.modules[name]

    # make sure we're doing an absolute import
    # name, path = make_absolute(name, path)
    
    if conf.addPaths:
        for p in path:
            add_path(p)

    path = [ p for p in path if p is not None ]
    cache = _modules.setdefault(':'.join(path), {})

    # quick exit for fully cached names
    if cache.has_key(name):
        return cache[name]
    
    parts = name.split('.')
    fqname = ''
    mod = parent = fh = None
    
    for part in parts:
        if fqname == '':
            fqname = part
        else:
            fqname = "%s.%s" % (fqname, part)

        if cache.has_key(fqname):
            mod = cache[fqname]
        else:
            try:
                acquire_lock()
                log.debug("find module part %s (%s) at %s", part, fqname, path)
                fh, filename, desc = find_module(part, path)
                old = sys.modules.get(fqname)
                if old:
                    # test modules frequently have name overlap; make sure
                    # we get a fresh copy of anything we are trying to load
                    # from a new path
                    if hasattr(old,'__path__'):
                        old_path = os.path.normpath(old.__path__[0])
                        old_ext = None
                    elif hasattr(old, '__file__'):
                        old_norm = os.path.normpath(old.__file__)
                        old_path, old_ext = os.path.splitext(old_norm)
                    else:
                        # builtin or other module-like object that
                        # doesn't have __file__
                        old_path, old_ext, old_norm = None, None, None
                    new_norm = os.path.normpath(filename)
                    new_path, new_ext = os.path.splitext(new_norm)
                    if old_path == new_path:
                        log.debug("module %s already loaded "
                                  "old: %s %s new: %s %s", fqname, old_path,
                                  old_ext, new_path, new_ext)
                        cache[fqname] = mod = old
                        continue
                    else:
                        del sys.modules[fqname]
                log.debug("Loading %s from %s", fqname, filename)
                mod = load_module(fqname, fh, filename, desc)
                log.debug("%s from %s yields %s", fqname, filename, mod)
                cache[fqname] = mod
            finally:
                if fh:
                    fh.close()
                release_lock()
        if parent:
            setattr(parent, part, mod)
        if hasattr(mod, '__path__'):
            path = mod.__path__
        parent = mod
    return mod

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
