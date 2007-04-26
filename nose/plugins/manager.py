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
           'BuiltinPluginManager', 'RestrictedPluginManager']

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
        log.debug("Configuring plugins")
        self.config = config
        cfg = PluginProxy('configure', self._plugins)
        cfg(options, config)
        enabled = [plug for plug in self._plugins if plug.enabled]
        enabled.sort(
            lambda a, b: cmp(getattr(a, 'score', 1), getattr(b, 'score', 1)))
        self.plugins = enabled
        log.debug("Plugins enabled: %s", enabled)

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
        # special case -- load tests from names behaves somewhat differently
        # from other chainable calls, because plugins return a tuple, only
        # part of which can be chained to the next plugin.
        if self.call == 'loadTestsFromNames':
            return self._loadTestsFromNames(*arg, **kw)
        try:
            meth = getattr(self.interface, self.call)
        except AttributeError:
            raise AttributeError("%s is not a valid %s method"
                                 % (self.call, self.interface.__name__))
        if getattr(meth, 'generative', False):
            # call all plugins and yield a flattened iterator of their results
            return list(self.generate(*arg, **kw))
        elif getattr(meth, 'chainable', False):
            return self.chain(*arg, **kw)
        else:
            # return a value from the first plugin that returns non-None
            return self.simple(*arg, **kw)

    # FIXME optimization: on first call, cache list of plugins with the method
    # and use that list only on each successive call
    
    def chain(self, *arg, **kw):
        """Call plugins in a chain, where the result of each plugin call is
        sent to the next plugin as input. The final output result is returned.
        """
        result = None
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(*arg, **kw)
            arg = (result,)
        return result

    def generate(self, *arg, **kw):
        """Call all plugins, yielding each item in each non-None result.
        """
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(*arg, **kw)
            if result is not None:
                for r in result:
                    yield r

    def simple(self, *arg, **kw):
        """Call all plugins, returning the first non-None result.
        """
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(*arg, **kw)
            if result is not None:
                return result

    def _loadTestsFromNames(self, names, module=None):
        """Chainable but not quite normal. Plugins return a tuple of
        (tests, names) after processing the names. The tests are added
        to a suite that is accumulated throughout the full call, while
        names are input for the next plugin in the chain.
        """
        suite = []
        for p in self.plugins:
            meth = getattr(p, self.call, None)
            if meth is None:
                continue
            result = meth(names, module=module)
            if result is not None:
                suite_part, names = result
                if suite_part:
                    suite.extend(suite_part)
        return suite, names

class ZeroNinePlugin:
    """Proxy for 0.9 plugins, adapts 0.10 calls to 0.9 standard.
    """
    def __init__(self, plugin):
        self.plugin = plugin

    def options(self, parser, env=os.environ):
        self.plugin.add_options(parser, env)
    
    def addError(self, test, err):
        if not hasattr(self.plugin, 'addError'):
            return
        # switch off to addSkip, addDeprecated if those types
        from nose.exc import SkipTest, DeprecatedTest
        ec, ev, tb = err
        if issubclass(ec, SkipTest):
            if not hasattr(self.plugin, 'addSkip'):
                return
            return self.plugin.addSkip(test.test)
        elif issubclass(ec, DeprecatedTest):
            if not hasattr(self.plugin, 'addDeprecated'):
                return
            return self.plugin.addDeprecated(test.test)           
        # add capt
        capt = test.capturedOutput
        return self.plugin.addError(test.test, err, capt)

    # FIXME loadTestsFromFile -> loadTestsFromPath

    def addFailure(self, test, err):
        if not hasattr(self.plugin, 'addFailure'):
            return
        # add capt and tbinfo
        capt = test.capturedOutput
        tbinfo = test.tbinfo
        return self.plugin.addFailure(test.test, err, capt, tbinfo)

    def addSuccess(self, test):
        if not hasattr(self.plugin, 'addSuccess'):
            return
        capt = test.capturedOutput
        self.plugin.addSuccess(test.test, capt)

    def startTest(self, test):
        if not hasattr(self.plugin, 'startTest'):
            return
        return self.plugin.startTest(test.test)

    def stopTest(self, test):
        if not hasattr(self.plugin, 'stopTest'):
            return
        return self.plugin.stopTest(test.test)

    def __getattr__(self, val):
        return getattr(self.plugin, val)

            
class EntryPointPluginManager(PluginManager):
    entry_points = (('nose.plugins.0-10', None),
                    ('nose.plugins', ZeroNinePlugin))
    
    def loadPlugins(self):
        """Load plugins by iterating the `nose.plugins` entry point.
        """
        super(EntryPointPluginManager, self).loadPlugins()
        from pkg_resources import iter_entry_points

        loaded = {}
        for entry_point, adapt in self.entry_points:
            for ep in iter_entry_points(entry_point):
                if ep.name in loaded:
                    continue
                loaded[ep.name] = True
                log.debug('%s load plugin %s', self.__class__.__name__, ep)
                try:
                    plugcls = ep.load()
                except KeyboardInterrupt:
                    raise
                except Exception, e:
                    # never want a plugin load to kill the test run
                    # but we can't log here because the logger is not yet
                    # configured
                    warn("Unable to load plugin %s: %s" % (ep, e),
                         RuntimeWarning)
                    continue
                if adapt:
                    plug = adapt(plugcls())
                else:
                    plug = plugcls
                self.addPlugin(plug)


class BuiltinPluginManager(PluginManager):
    def loadPlugins(self):
        """Load plugins in nose.plugins.builtin
        """
        super(BuiltinPluginManager, self).loadPlugins()
        from nose.plugins import builtin
        for plug in builtin.plugins:
            self.addPlugin(plug())
        
try:
    import pkg_resources
    class DefaultPluginManager(BuiltinPluginManager, EntryPointPluginManager):
        pass
except ImportError:
    DefaultPluginManager = BuiltinPluginManager


class RestrictedPluginManager(DefaultPluginManager):
    """Plugin manager that restricts the plugin list to those not
    excluded by a list of exclude methods. Any plugin that implements
    an excluded method will be removed from the manager's plugin list
    after plugins are loaded.
    """
    def __init__(self, plugins=(), exclude=()):
        DefaultPluginManager.__init__(self, plugins)
        self.exclude = exclude

    def loadPlugins(self):
        DefaultPluginManager.loadPlugins(self)
        allow = []
        for plugin in self.plugins:
            ok = True
            for method in self.exclude:
                if hasattr(plugin, method):
                    warn("Exclude plugin %s: implements %s" % (plugin, method),
                         RuntimeWarning)
                    ok = False
                    break
            if ok:
                allow.append(plugin)
        self.plugins = allow

    
