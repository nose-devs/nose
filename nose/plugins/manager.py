"""
Plugin Manager
--------------

The default plugin manager class is used to load plugins and proxy calls
to plugins.

"""
from nose.plugins.base import IPluginInterface

class PluginManager(object):

    def __init__(self, plugins=()):
        self._plugins = []
        if plugins:
            self.addPlugins(plugins)

    def __getattr__(self, call):
        return PluginProxy(call, self._plugins)

    def addPlugin(self, plug):
        self._plugins.append(plug)

    def addPlugins(self, plugins):
        for plug in plugins:
            self.addPlugin(plug)

    def get_plugins(self):
        return self._plugins

    def loadPlugins(self):
        raise NotImplementedError("loadPlugins not implemented")

    def set_plugins(self, plugins):
        self._plugins = []
        self.addPlugins(plugins)

    plugins = property(get_plugins, set_plugins, None,
                       """Access the list of plugins managed by
                       this plugin manager""")


class PluginProxy(object):
    """Proxy for plugin calls. Essentially a closure bound to the
    given call and plugin list.
    """

    def __init__(self, call, plugins):
        self.call = call
        self.plugins = plugins[:]

    
    def __call__(self, *arg, **kw):
        try:
            meth = getattr(IPluginInterface, self.call)
        except AttributeError:
            raise AttributeError("%s is not a valid plugin method" % self.call)
        if getattr(meth, 'generative', False):
            # call all plugins and return a flattened list of their results
            return self.generate(*arg, **kw)
        else:
            # return a value from the first plugin that returns non-None
            return self.simple(*arg, **kw)

    def generate(self, *arg, **kw):
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(*arg, **kw)
            if result is not None:
                for r in result:
                    yield r

    def simple(self, *arg, **kw):
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(*arg, **kw)
            if result is not None:
                return result

            
