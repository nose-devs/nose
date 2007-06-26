#!/usr/bin/env python

import os
import time
from docutils.core import publish_string, publish_parts
from docutils.readers.standalone import Reader
from pudge.browser import Browser
from epydoc.objdoc import _lookup_class_field
import inspect
import nose
import textwrap
from optparse import OptionParser
from nose.util import resolve_name, odict

## FIXME: menu needs sections

def defining_class(cls, attr):
    val, container = _lookup_class_field(cls, attr)
    return container.value()


def write(filename, tpl, ctx):
    print filename
    fp = open(filename, 'w')
    fp.write(tpl % ctx)
    fp.close()


def doc_word(node):

    # FIXME handle links like package.module and module.Class
    
    print "Unknown ref %s" % node.astext()    
    node['refuri'] = '_'.join(
        map(lambda s: s.lower(), node.astext().split(' '))) + '.html'
    del node['refname']
    node.resolved = True
    return True
doc_word.priority = 100



class DocReader(Reader):
    unknown_reference_resolvers = (doc_word,)


def formatargspec(func, exclude=()):
    try:
        args, varargs, varkw, defaults = inspect.getargspec(func)
    except TypeError:
        return "(...)"
    if defaults:
        defaults = map(clean_default, defaults)
    for a in exclude:
        if a in args:
            ix = args.index(a)
            args.remove(a)
            try:
                defaults.pop(ix)
            except AttributeError:
                pass
    return inspect.formatargspec(
        args, varargs, varkw, defaults).replace("'os.environ'", 'os.environ')


def clean_default(val):
    if isinstance(val, os._Environ):
        return 'os.environ'
    return val


def to_html(rst):
    parts = publish_parts(rst, reader=DocReader(), writer_name='html')
    return parts['body']


def document_module(mod):
    name = mod.qualified_name()
    print name
    body =  to_html(mod.doc())

    # FIXME prepend with note on what highlighted means

    # FIXME need to have some notion of aliased classes
    # eg defaultSelector = Selector, and modules
    # should be able to set order of classes in docs

    # classes
    classes = [document_class(cls) for cls in get_classes(mod)]
    if classes:
        body += '<h2>Classes</h2>\n' + '\n'.join(classes)

    # functions
    funcs = [document_function(func) for func in mod.routines()]
    if funcs:
        body += '<h2>Functions</h2>\n' + '\n'.join(funcs)

    # FIXME attributes

    # FIXME add classes, funcs and attributes to submenu

    pg = {'body': body,
          'title': name}
    pg.update(std_info)
    to_write.append(('Module: %s' % name,
                     os.path.join(doc, 'module_%s.html' % name),
                     tpl, pg))    


def get_classes(mod):
    # some "invisible" items I do want, but not others
    # really only those classes defined in the module itself
    # with some per-module alias list handling (eg,
    # TestLoader and defaultTestLoader shouldn't both be fully doc'd)
    all = list(mod.classes(visible_only=0))

    # sort by place in __all__
    names = odict() # list comprehension didn't work? possible bug in odict
    for c in all:
        if c is not None and not c.isalias():
            names[c.name] = c
    ordered = []
    try:
        for name in mod.obj.__all__:
            if name in names:
                cls = names[name]
                del names[name]
                if cls is not None:
                    ordered.append(cls)
    except AttributeError:
        pass    
    for name, cls in names.items():
        ordered.append(cls)
    wanted = []
    classes = set([])
    for cls in ordered:
        if cls.obj in classes:
            cls.alias_for = cls.obj
        else:
            classes.add(cls.obj)
        wanted.append(cls)    
    return wanted


def document_class(cls):
    print "  %s" % cls.qualified_name()
    alias = False
    if hasattr(cls, 'alias_for'):
        alias = True
        doc = '(Alias for %s)' % link_to_class(cls.alias_for)
    else:
        doc = to_html(cls.doc())
    bases = ', '.join(link_to_class(c) for c in cls.obj.__bases__)
    html = ['<a name="%s"></a><div class="cls section">' % cls.name,
            '<span class="cls name">%s</span> (%s)' % (cls.name, bases),
            '<div class="cls doc">%s' % doc]

    if not alias:
        real_class = cls.obj
        methods = list(cls.routines(visible_only=False))
        if methods:
            methods.sort(lambda a, b: cmp(a.name, b.name))
            html.append('<h4>Methods</h4>')
            for method in methods:
                print "    %s" % method.qualified_name()
                defined_in = defining_class(real_class, method.name)
                if defined_in == real_class:
                    inherited = ''
                    inh_cls = ''
                else:
                    inherited = '<span class="method inherited">' \
                                '(FIXME: inherited from %s)</span>' \
                                % defined_in.__name__
                    inh_cls = ' inherited'
                html.extend([
                    '<div class="method section%s">' % inh_cls, 
                    '<span class="method name">%s</span>' % method.name,
                    '<span class="method args">%s</span>'
                    % formatargspec(method.obj),
                    inherited,
                    '<div class="method doc">%s</div>' % to_html(method.doc()),
                    '</div>'])

        attrs = list(cls.attributes(visible_only=False))
        if attrs:
            attrs.sort(lambda a, b: cmp(a.name, b.name))
            html.append('<h4>Attributes</h4>')
            for attr in attrs:
                if defined_in == real_class:
                    inherited = ''
                    inh_cls = ''
                else:
                    inherited = '<span class="attr inherited">' \
                                '(FIXME: inherited from %s)</span>' \
                                % defined_in.__name__
                    inh_cls = ' inherited'
                html.extend([
                    '<div class="attr section%s">' % inh_cls,
                    '<span class="attr name">%s</span>' % attr.name,
                    '<span class="attr value">%(a)s</span>' %
                    {'a': getattr(attr.parent.obj, attr.name)},
                    '<div class="attr doc">%s</div>' % to_html(attr.doc()),
                    '</div>'])

    html.append('</div></div>')

    return ''.join(html)


def document_function(func):
    print "  %s" % func.name
    html = [
        '<a name="%s"></a><div class="func section">' % func.name,
        '<span class="func name">%s</span>' % func.name,
        '<span class="func args">%s</span>'
        % formatargspec(func.obj, exclude=['self']),
        '<div class="func doc">%s</div>' % to_html(func.doc()),
        '</div>']
    return ''.join(html)


def link_to_class(cls):
    mod = cls.__module__
    name = cls.__name__
    if mod.startswith('_'):
        qname = name
    else:
        qname = "%s.%s" % (mod, name)
    if not mod.startswith('nose'):
        return qname
    return '<a href="module_%s.html#%s">%s</a>' % (mod, name, name)


root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
doc = os.path.join(root, 'doc')
tpl = open(os.path.join(doc, 'doc.html.tpl'), 'r').read()
api_tpl = open(os.path.join(doc, 'plugin_api.html.tpl'), 'r').read()
plug_tpl = open(os.path.join(doc, 'plugin.html.tpl'), 'r').read()
std_info = {
    'version': nose.__version__,
    'date': time.ctime()
    }
to_write = []

# FIXME the main menu contents aren't known until all plugins have been
# doc'd so delay page output for all pages until the end.

# plugins
from nose import plugins
from nose.plugins.base import IPluginInterface
from nose.plugins import errorclass

# writing plugins guide
writing_plugins = {'body': to_html(plugins.__doc__)}
writing_plugins.update(std_info)
writing_plugins.update({'title': 'Writing Plugins',
                        'menu': 'FIXME -- menu'})
to_write.append(
    ('Writing Plugins',
     os.path.join(doc, 'writing_plugins.html'), tpl, writing_plugins))


# error class plugins
ecp = {'body': to_html(errorclass.__doc__)}
ecp.update(std_info)
ecp.update({'title': 'ErrorClass Plugins',
                        'menu': 'FIXME -- menu'})
to_write.append(
    ('ErrorClass Plugins',
     os.path.join(doc, 'errorclassplugin.html'), tpl, ecp))

# interface
itf = {'body': to_html(textwrap.dedent(IPluginInterface.__doc__))}

# methods
attr = [(a, getattr(IPluginInterface, a)) for a in dir(IPluginInterface)]
methods = [m for m in attr if inspect.ismethod(m[1])]
methods.sort()
# print "Documenting methods", [a[0] for a in methods]

method_html = []
method_tpl = """
<div class="method %(extra_class)s">
<a name="%(name)s">
<span class="name">%(name)s</span><span class="arg">%(arg)s</span></a>
<div class="doc">%(body)s</div>
</div>
"""

menu_links = {}

m_attrs = ('_new', 'changed', 'deprecated', 'generative', 'chainable')
for m in methods:
    name, meth = m
    ec = []
    for att in m_attrs:
        if hasattr(meth, att):
            ec.append(att.replace('_', ''))
            menu_links.setdefault(att.replace('_', ''), []).append(name)
    # padding evens the lines
    print name
    mdoc = {'body': to_html(textwrap.dedent('        ' + meth.__doc__))}
    argspec = formatargspec(meth)
    mdoc.update({'name': name,
                 'extra_class': ' '.join(ec),
                 'arg': argspec})
    method_html.append(method_tpl % mdoc)

itf['methods'] = ''.join(method_html)
itf.update(std_info)
itf['title'] = 'Plugin Interface'

menu = []
for section in ('new', 'changed', 'deprecated'):
    menu.append('<h2>%s methods</h2>' % section.title())
    menu.append('<ul><li>')
    menu.append('</li><li>'.join([
        '<a href="%(name)s">%(name)s</a>' % {'name': n}
        for n in menu_links[section]]))
    menu.append('</li></ul>')
itf['sub_menu'] = ''.join(menu)

to_write.append(
    ('Plugin Interface',
     os.path.join(doc, 'plugin_interface.html'), api_tpl, itf))


# individual plugin usage docs
from nose.plugins.builtin import builtins

pmeths = [m[0] for m in methods[:]
          if not 'options' in m[0].lower()]
pmeths.append('options')
pmeths.sort()

for modulename, clsname in builtins:
    _, _, modname = modulename.split('.')
    mod = resolve_name(modulename)
    cls = getattr(mod, clsname)
    filename = os.path.join(doc, 'plugin_%s.html' % modname)
    print modname, filename
    if not mod.__doc__:
        print "No docs"
        continue
    pdoc = {'body': to_html(mod.__doc__)}
    pdoc.update(std_info)
    pdoc['title'] = 'builtin plugin: %s' % modname

    # options
    parser = OptionParser(add_help_option=False)
    plug = cls()
    plug.addOptions(parser)
    options = parser.format_option_help()
    pdoc['options'] = options

    # hooks used
    hooks = []
    for m in pmeths:
        if getattr(cls, m, None):
            hooks.append('<li><a href="plugin_interface.html#%(name)s">'
                         '%(name)s</a></li>' % {'name': m})
    pdoc['hooks'] = ''.join(hooks)
            
    to_write.append(
        ('Builtin Plugin: %s' % modname,
         os.path.join(doc, filename), plug_tpl, pdoc))


# individual module docs
b = Browser(['nose','nose.plugins.manager'],
            exclude_modules=['nose.plugins', 'nose.ext'])
for mod in b.modules(recursive=1):
    if mod.name == 'nose':
        # no need to regenerate, this is the source of the doc index page
        continue
    print mod.qualified_name()
    document_module(mod)

    
menu = [ '<li><a href="%s">%s</a></li>' % (os.path.basename(filename), title)
         for title, filename, _, _ in to_write ]
menu.insert(0, '<ul>')
menu.insert(0, '<h2>Documentation</h2>')
menu.append('</ul>')

menu = ''.join(menu)
for title, filename, template, ctx in to_write:
    ctx['menu'] = menu
    write(filename, template, ctx)



#write(doc, tpl, 'writing_plugins.html', plugins.__doc__)
#write(doc, tpl, 'plugin_interface.html', IPluginInterface


