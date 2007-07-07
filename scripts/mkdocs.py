#!/usr/bin/env python

import os
import re
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


remove_at = re.compile(r' at 0x[0-9a-f]+')


def defining_class(cls, attr):
    val, container = _lookup_class_field(cls, attr)
    return container.value()


def write(filename, tpl, ctx):
    print filename
    ctx.setdefault('submenu', '')
    fp = open(filename, 'w')
    fp.write(tpl % ctx)
    fp.close()


def doc_word(node):

    # handle links like package.module and module.Class
    # as wellas 'foo bar'
    
    name = node.astext()
    print "Unknown ref %s" % name
    if '.' in name:

        parts = name.split('.')
        # if the first letter of a part is capitalized, assume it's
        # a class name, and put all parts from that part on into
        # the anchor part of the link
        link, anchor = [], []
        addto = link
        while parts:
            part = parts.pop(0)
            if addto == link and part[0].upper() == part[0]:
                addto = anchor
            addto.append(part)
        node['refuri'] = 'module_' + '.'.join(link) + '.html'
        if anchor:
            node['refuri'] += '#' + '.'.join(anchor)
    else:
        node['refuri'] = '_'.join(
            map(lambda s: s.lower(), name.split(' '))) + '.html'
                
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

    # for classes: prepend with note on what highlighted means
    cls_note = "<p>Highlighted methods are defined in this class.</p>"

    submenu = []

    # classes
    mod_classes = get_classes(mod)
    classes = [document_class(cls) for cls in mod_classes]
    if classes:
        body += '<h2>Classes</h2>\n' + cls_note + '\n'.join(classes)
        submenu.extend(make_submenu('Classes', mod_classes))
        
    # functions
    mod_funcs = list(mod.routines())
    funcs = [document_function(func) for func in mod_funcs]
    if funcs:
        body += '<h2>Functions</h2>\n' + '\n'.join(funcs)
        submenu.extend(make_submenu('Functions', mod_funcs))
            
    # attributes
    mod_attrs = list(mod.attributes())
    attrs = [document_attribute(attr) for attr in mod_attrs]
    if attrs:
        body += '<h2>Attributes</h2>\n' + '\n'.join(attrs)
        submenu.extend(make_submenu('Attributes', mod_attrs))
        
    pg = {'body': body,
          'title': name,
          'submenu': ''.join(submenu)}
    pg.update(std_info)
    to_write.append((
        'Modules',
        'Module: %s' % name,
        os.path.join(doc, 'module_%s.html' % name),
        tpl, pg))    


def make_submenu(name, objs):
    sm = ['<h2>%s</h2>' % name, '<ul>']
    sm.extend(['<li><a href="#%s">%s</a></li>' % (o.name, o.name)
               for o in objs] + ['</ul>'])
    return sm

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
            html.append('<h3>Methods</h3>')
            for method in methods:
                print "    %s" % method.qualified_name()
                defined_in = defining_class(real_class, method.name)
                if defined_in == real_class:
                    inherited = ''
                    inh_cls = ''
                else:
                    inherited = '<span class="method inherited">' \
                                '(inherited from %s)</span>' \
                                % defined_in.__name__
                    inh_cls = ' inherited'
                html.extend([
                    '<div class="method section%s">' % inh_cls, 
                    '<span class="method name">%s' % method.name,
                    '<span class="args">%s</span></span>'
                    % formatargspec(method.obj),
                    inherited,
                    '<div class="method doc">%s</div>' % to_html(method.doc()),
                    '</div>'])

        attrs = list(cls.attributes(visible_only=False))
        if attrs:
            attrs.sort(lambda a, b: cmp(a.name, b.name))
            html.append('<h3>Attributes</h3>')
            for attr in attrs:
                print "    a %s" % attr.qualified_name()
                defined_in = defining_class(real_class, attr.name)
                if defined_in == real_class:
                    inherited = ''
                    inh_cls = ''
                else:
                    inherited = '<span class="attr inherited">' \
                                '(inherited from %s)</span>' \
                                % defined_in.__name__
                    inh_cls = ' inherited'
                val = format_attr(attr.parent.obj, attr.name)
                html.extend([
                    '<div class="attr section%s">' % inh_cls,
                    '<span class="attr name">%s</span>' % attr.name,
                    '<pre class="attr value">Default value: %(a)s</pre>' %
                    {'a': val},
                    '<div class="attr doc">%s</div>' % to_html(attr.doc()),
                    '</div>'])

    html.append('</div></div>')

    return ''.join(html)


def document_function(func):
    print "  %s" % func.name
    html = [
        '<a name="%s"></a><div class="func section">' % func.name,
        '<span class="func name">%s' % func.name,
        '<span class="args">%s</span></span>'
        % formatargspec(func.obj, exclude=['self']),
        '<div class="func doc">%s</div>' % to_html(func.doc()),
        '</div>']
    return ''.join(html)


def document_attribute(attr):
    print "  %s" % attr.name
    value = format_attr(attr.parent.obj, attr.name)
    html = [
        '<a name="%s"></a><div class="attr section">' % attr.name,
        '<span class="attr name">%s</span>' % attr.name,
        '<pre class="attr value">Default value: %(a)s</pre>' %
        {'a': value},
        '<div class="attr doc">%s</div>' % to_html(attr.doc()),
        '</div>']
    return ''.join(html)


def format_attr(obj, attr):
    val = getattr(obj, attr)
    if isinstance(val, property):
        # value makes no sense when it's a property
        return '(property)'
    val = str(val).replace(
        '&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(
        '"', '&quot;').replace("'", '&#39;')
    val = remove_at.sub('', val)
    return val

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


# plugins
from nose import plugins
from nose.plugins.base import IPluginInterface
from nose.plugins import errorclass

# writing plugins guide
writing_plugins = {'body': to_html(plugins.__doc__)}
writing_plugins.update(std_info)
writing_plugins['title'] = 'Writing Plugins'
to_write.append(
    ('Plugins',
     'Writing Plugins',
     os.path.join(doc, 'writing_plugins.html'), tpl, writing_plugins))


# error class plugins
ecp = {'body': to_html(errorclass.__doc__)}
ecp.update(std_info)
ecp['title'] = 'ErrorClass Plugins'
to_write.append(
    ('Plugins',
     'ErrorClass Plugins',
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
    ('Plugins',
     'Plugin Interface',
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
        ('Plugins',
         'Builtin Plugin: %s' % modname,
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


# finally build the menu and write all pages
menu = []
sections = odict()
for page in to_write:
    section, _, _, _, _ = page
    sections.setdefault(section, []).append(page)

for section, pages in sections.items():
    menu.append('<h2>%s</h2>' % section)
    menu.append('<ul>')
    pages.sort()
    menu.extend([
        '<li><a href="%s">%s</a></li>' % (os.path.basename(filename), title)
        for _, title, filename, _, _ in pages ])
    menu.append('</ul>')

menu = ''.join(menu)
for section, title, filename, template, ctx in to_write:
    ctx['menu'] = menu
    write(filename, template, ctx)

# doc section index page
idx_tpl = open(os.path.join(doc, 'index.html.tpl'), 'r').read()
idx = {
    'title': 'API documentation',
    'menu': menu}
idx.update(std_info)
write(os.path.join(doc, 'index.html'), idx_tpl, idx)

