#!/usr/bin/env python

import os
import time
from docutils.core import publish_string, publish_parts
from docutils.readers.standalone import Reader
import inspect
import nose
import textwrap

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
    print "clean default %s (%s) %s" % (val, type(val), val.__class__)
    if isinstance(val, os._Environ):
        return '{...}'
    return val

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
doc = os.path.join(root, 'doc')
tpl = open(os.path.join(doc, 'doc.html.tpl'), 'r').read()

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
<span class="name">%(name)s</span><span class="arg">%(arg)s</span><br />
%(body)s
</div>
"""


m_attrs = ('_new', 'changed', 'deprecated', 'generative', 'chainable')
for m in methods:
    name, meth = m
    ec = []
    for att in m_attrs:
        if hasattr(m, att):
            ec.append(att)
    # padding evens the lines
    mdoc = publish_parts(textwrap.dedent('        ' + meth.__doc__),
                         writer_name='html')
    args, varargs, varkw, defaults = inspect.getargspec(meth)
    if defaults:
        defaults = map(clean_default, defaults)
    mdoc.update({'name': name,
                 'extra_class': ' '.join(ec),
                 'arg': inspect.formatargspec(args, varargs, varkw, defaults)})
    method_html.append(method_tpl % mdoc)

itf.update(std_info)
itf.update({'title': 'Plugin Interface',
            'menu': 'FIXME -- menu'})
itf['body'] += '\n'.join(method_html)
write(os.path.join(doc, 'plugin_interface.html'), tpl % itf)


#write(doc, tpl, 'writing_plugins.html', plugins.__doc__)
#write(doc, tpl, 'plugin_interface.html', IPluginInterface


