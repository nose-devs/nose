#!/usr/bin/env python

import os
import time
from docutils.core import publish_string, publish_parts
from docutils.readers.standalone import Reader
import inspect
import nose
import textwrap
from optparse import OptionParser
from nose.util import resolve_name


def write(filename, content):
    print filename
    fp = open(filename, 'w')
    fp.write(content)
    fp.close()


def doc_word(node):
    print "Unknown ref %s" % node.astext()    
    node['refuri'] = '_'.join(
        map(lambda s: s.lower(), node.astext().split(' '))) + '.html'
    del node['refname']
    node.resolved = True
    return True
doc_word.priority = 100



class DocReader(Reader):
    unknown_reference_resolvers = (doc_word,)


def clean_default(val):
    if isinstance(val, os._Environ):
        return 'os.environ'
    return val

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
doc = os.path.join(root, 'doc')
tpl = open(os.path.join(doc, 'doc.html.tpl'), 'r').read()
api_tpl = open(os.path.join(doc, 'plugin_api.html.tpl'), 'r').read()

std_info = {
    'version': nose.__version__,
    'date': time.ctime()
    }

# plugins
from nose import plugins
from nose.plugins.base import IPluginInterface

# writing plugins guide
writing_plugins = publish_parts(plugins.__doc__, reader=DocReader(),
                                writer_name='html')
writing_plugins.update(std_info)
writing_plugins.update({'title': 'Writing Plugins',
                        'menu': 'FIXME -- menu'})
write(os.path.join(doc, 'writing_plugins.html'), tpl % writing_plugins)

# interface
itf = publish_parts(textwrap.dedent(IPluginInterface.__doc__),
                    reader=DocReader(),
                    writer_name='html')

# methods
attr = [(a, getattr(IPluginInterface, a)) for a in dir(IPluginInterface)]
methods = [m for m in attr if inspect.ismethod(m[1])]
methods.sort()
print "Documenting methods", [a[0] for a in methods]

method_html = []
method_tpl = """
<div class="method %(extra_class)s">
<span class="name">%(name)s</span><span class="arg">%(arg)s</span>
<div class="doc">%(body)s</div>
</div>
"""


m_attrs = ('_new', 'changed', 'deprecated', 'generative', 'chainable')
for m in methods:
    name, meth = m
    ec = []
    for att in m_attrs:
        if hasattr(meth, att):
            ec.append(att.replace('_', ''))
    # padding evens the lines
    mdoc = publish_parts(textwrap.dedent('        ' + meth.__doc__),
                         writer_name='html')
    args, varargs, varkw, defaults = inspect.getargspec(meth)
    if defaults:
        defaults = map(clean_default, defaults)
    argspec = inspect.formatargspec(
        args, varargs, varkw, defaults).replace("'os.environ'", 'os.environ')
    mdoc.update({'name': name,
                 'extra_class': ' '.join(ec),
                 'arg': argspec})
    method_html.append(method_tpl % mdoc)

itf['methods'] = ''.join(method_html)
itf.update(std_info)
itf.update({'title': 'Plugin Interface',
            'menu': 'FIXME -- menu'})

write(os.path.join(doc, 'plugin_interface.html'), api_tpl % itf)


# individual plugin usage docs
from nose.plugins.builtin import builtins

for modulename, clsname in builtins:
    _, _, modname = modulename.split('.')
    mod = resolve_name(modulename)
    cls = getattr(mod, clsname)
    filename = os.path.join(doc, 'plugin_%s.html' % modname)
    print modname, filename
    if not mod.__doc__:
        print "No docs"
        continue
    pdoc = publish_parts(mod.__doc__, reader=DocReader(), writer_name='html')
    pdoc.update(std_info)
    pdoc.update({'title': 'builtin plugin: %s' % modname,
                 'menu': 'FIXME -- menu'})

    parser = OptionParser()
    plug = cls()
    plug.addOptions(parser)
    options = parser.format_option_help()

    pdoc['body'] = pdoc['body'] + '<pre>' + options + '</pre>'
    write(os.path.join(doc, filename), tpl % pdoc)



#write(doc, tpl, 'writing_plugins.html', plugins.__doc__)
#write(doc, tpl, 'plugin_interface.html', IPluginInterface


