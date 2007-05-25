#!/usr/bin/env python

from docutils.core import publish_string, publish_parts
from docutils.readers.standalone import Reader
from nose.config import Config
from nose.plugins.manager import BuiltinPluginManager
import nose
import nose.commands
import nose.tools
import os
import re
import time

def doc_word(node):
    print "Unknown ref %s" % node.astext()    
    node['refuri'] = 'doc/' \
        + '_'.join(map(lambda s: s.lower(), node.astext().split(' '))) \
        + '.html'
    del node['refname']
    node.resolved = True
    return True
doc_word.priority = 100

class DocReader(Reader):
    unknown_reference_resolvers = (doc_word,)


root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print "Main..."
tpl = open(os.path.join(root, 'index.html.tpl'), 'r').read()

pat = re.compile(r'^.*(Basic usage)', re.DOTALL)
txt = nose.__doc__.replace(':: python','::')
txt = pat.sub(r'\1', txt)

# cut from 'about the name' down (goes to end of page)
pat = re.compile(r'^(.*?)(About the name.*$)', re.DOTALL)
txt, coda = pat.search(txt).groups()

docs = publish_parts(txt, reader=DocReader(), writer_name='html')
docs.update({'version': nose.__version__,
             'date': time.ctime()})
docs['coda'] = publish_parts(coda, writer_name='html')['body']

#print "Tools..."
#tools = publish_parts(nose.tools.__doc__, writer_name='html')
#docs['tools'] = tools['body']

print "Commands..."
cmds = publish_parts(nose.commands.__doc__, reader=DocReader(),
                     writer_name='html')
docs['commands'] = cmds['body']

print "Changelog..."
changes = open(os.path.join(root, 'CHANGELOG'), 'r').read()
changes_html = publish_parts(changes, reader=DocReader(), writer_name='html')
docs['changelog'] = changes_html['body']

print "News..."
news = open(os.path.join(root, 'NEWS'), 'r').read()
news_html = publish_parts(news, reader=DocReader(), writer_name='html')
docs['news'] = news_html['body']

print "Usage..."
conf = Config(plugins=BuiltinPluginManager())
usage_txt = conf.help(nose.main.__doc__).replace(
    'mkindex.py', 'nosetests')
docs['usage'] = '<pre>%s</pre>' % usage_txt

out = tpl % docs

index = open(os.path.join(root, 'index.html'), 'w')
index.write(out)
index.close()

readme = open(os.path.join(root, 'README.txt'), 'w')
readme.write(nose.__doc__)
readme.close()
