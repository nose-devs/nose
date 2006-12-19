#!/usr/bin/env python

from docutils.core import publish_string, publish_parts
import nose
import nose.commands
import nose.tools
import os
import re
import time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print "Main..."
tpl = open(os.path.join(root, 'index.html.tpl'), 'r').read()

pat = re.compile(r'^.*(Basic usage)', re.DOTALL)
txt = nose.__doc__.replace(':: python','::')
txt = pat.sub(r'\1', txt)
docs = publish_parts(txt, writer_name='html')
docs.update({'version': nose.__version__,
             'date': time.ctime()})

print "Tools..."
tools = publish_parts(nose.tools.__doc__, writer_name='html')
docs['tools'] = tools['body']

print "Commands..."
cmds = publish_parts(nose.commands.__doc__, writer_name='html')
docs['commands'] = cmds['body']

print "Changelog..."
changes = open(os.path.join(root, 'CHANGELOG'), 'r').read()
changes_html = publish_parts(changes, writer_name='html')
docs['changelog'] = changes_html['body']

print "News..."
news = open(os.path.join(root, 'NEWS'), 'r').read()
news_html = publish_parts(news, writer_name='html')
docs['news'] = news_html['body']

print "Usage..."
usage_txt = nose.configure(help=True).replace('mkindex.py', 'nosetests')
# FIXME remove example plugin & html output parts
docs['usage'] = '<pre>%s</pre>' % usage_txt

out = tpl % docs

index = open(os.path.join(root, 'index.html'), 'w')
index.write(out)
index.close()

readme = open(os.path.join(root, 'README.txt'), 'w')
readme.write(nose.__doc__)
readme.close()
