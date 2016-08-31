In python 3.4, a lot of the :mod:`imp` machinery has been rewritten. In
particular, the part that actually imports the module now acquire and release
the global import lock, so an explicit lock in
:meth:`nose.importer.Importer.importFromDir` is not needed and it's likely the
source of the deadlock reported in issue #921. This happen when a lock is
created somewhere at the module level or as static property of a class. E.g.::

  import multiprocessing

  manager = multiprocessing.Manager()
  lock = manager.Lock()
  dict_ = manager.dict()
