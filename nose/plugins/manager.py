"""
Plugin Manager
--------------

A plugin manager class is used to load plugins and proxy calls
to plugins.

* Built in
* Entry point

"""
import logging
import os
from warnings import warn
from nose.plugins.base import IPluginInterface

__all__ = ['DefaultPluginManager', 'PluginManager', 'EntryPointPluginManager',
           'BuiltinPluginManager']

log = logging.getLogger(__name__)

class PluginManager(object):

    def __init__(self, plugins=()):
        self._plugins = []
        if plugins:
            self.addPlugins(plugins)

    def __getattr__(self, call):
        return PluginProxy(call, self._plugins)

    def __iter__(self):
        return iter(self.plugins)

    def addPlugin(self, plug):
        self._plugins.append(plug)

    def addPlugins(self, plugins):
        for plug in plugins:
            self.addPlugin(plug)

    def configure(self, options, config):
        """Configure the set of plugins with the given options
        and config instance. After configuration, disabled plugins
        are removed from the plugins list.
        """
        self.config = config
        cfg = PluginProxy('configure', self._plugins)
        cfg(options, config)
        enabled = [plug for plug in self._plugins if plug.enabled]
        self.plugins = enabled        

    def loadPlugins(self):
        pass

    def _get_plugins(self):
        return self._plugins

    def _set_plugins(self, plugins):
        self._plugins = []
        self.addPlugins(plugins)

    plugins = property(_get_plugins, _set_plugins, None,
                       """Access the list of plugins managed by
                       this plugin manager""")


class PluginProxy(object):
    """Proxy for plugin calls. Essentially a closure bound to the
    given call and plugin list.
    """
    interface = IPluginInterface
    def __init__(self, call, plugins):
        self.call = call
        self.plugins = plugins[:]
    
    def __call__(self, *arg, **kw):
        try:
            meth = getattr(self.interface, self.call)
        except AttributeError:
            raise AttributeError("%s is not a valid %s method"
                                 % (self.call, self.interface.__name__))
        if getattr(meth, 'generative', False):
            # call all plugins and yield a flattened iterator of their results
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

            
class EntryPointPluginManager(PluginManager):
    entry_point = 'nose.plugins.0-10'
    
    def loadPlugins(self):
        """Load plugins by iterating the `nose.plugins` entry point.
        """
        super(EntryPointPluginManager, self).loadPlugins()
        from pkg_resources import iter_entry_points
        
        for ep in iter_entry_points(self.entry_point):
            log.debug('%s load plugin %s', self.__class__.__name__, ep)
            try:
                plug = ep.load()
            except KeyboardInterrupt:
                raise
            except Exception, e:
                # never want a plugin load to kill the test run
                # but we can't log here because the logger is not yet
                # configured
                warn("Unable to load plugin %s: %s" % (ep, e), RuntimeWarning)
                continue
            self.addPlugin(plug())


class BuiltinPluginManager(PluginManager):
    def loadPlugins(self):
        """Load plugins in nose.plugins.builtin
        """
        super(BuiltinPluginManager, self).loadPlugins()
        from nose.plugins import builtin
        for plug in builtin.plugins:
            self.addPlugin(plug())
        

class LegacyPluginManager(EntryPointPluginManager):
    """Loads 0.9 plugins and wraps each in a LegacyPlugin, which
    filters or rearranges the plugin calls that have changed since 0.9
    to call them as 0.9 did.
    """
    entry_point = 'nose.plugins'

    def addPlugin(self, plug):
        super(LegacyPluginManager, self).addPlugin(LegacyPlugin(plug))


class LegacyPlugin:
    """Proxy for 0.9 plugins, adapts 0.10 calls to 0.9 standard.
    """
    def __init__(self, plugin):
        self.plugin = plugin

    def options(self, parser, env=os.environ):
        # call add_options
        pass
    
    def addError(self, test, err):
        # add capt
        # switch off to addSkip, addDeprecated if those types
        pass

    def addFailure(self, test, err):
        # add capt, tb_info
        pass

    def __getattr__(self, val):
        return getattr(self.plugin, val)
    

try:
    import pkg_resources
    class DefaultPluginManager(BuiltinPluginManager, EntryPointPluginManager):
        pass
except ImportError:
    DefaultPluginManager = BuiltinPluginManager
