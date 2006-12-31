#!/usr/bin/env python

from commands import getstatusoutput
from docutils.core import publish_string, publish_parts
from docutils.nodes import SparseNodeVisitor
from docutils.writers import Writer
import nose
import os
import pudge.browser
import re
import sys
import textwrap
import time

# constants
success = 0
div = '\n----\n'
warning = """
*Do not edit above this line. Content above this line is automatically
generated and edits above this line will be discarded.*

= Comments =
"""

class WikiWriter(Writer):
    def translate(self):
        visitor = WikiVisitor(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()

        
class WikiVisitor(SparseNodeVisitor):
    def __init__(self, document):
        SparseNodeVisitor.__init__(self, document)
        self.list_depth = 0
        self.list_item_prefix = None
        self.indent = self.old_indent = ''
        self.output = []
        self.preformat = False
        
    def astext(self):
        return ''.join(self.output)

    def visit_Text(self, node):
        #print "Text", node
        data = node.astext()
        if not self.preformat:
            data = data.lstrip('\n\r')
            data = data.replace('\r', '')
            data = data.replace('\n', ' ')
        self.output.append(data)
    
    def visit_bullet_list(self, node):
        self.list_depth += 1
        self.list_item_prefix = (' ' * self.list_depth) + '* '

    def depart_bullet_list(self, node):
        self.list_depth -= 1
        if self.list_depth == 0:
            self.list_item_prefix = None
        else:
            (' ' * self.list_depth) + '* '
        self.output.append('\n\n')
                           
    def visit_list_item(self, node):
        self.old_indent = self.indent
        self.indent = self.list_item_prefix

    def depart_list_item(self, node):
        self.indent = self.old_indent
        
    def visit_literal_block(self, node):
        self.output.extend(['{{{', '\n'])
        self.preformat = True

    def depart_literal_block(self, node):
        self.output.extend(['\n', '}}}', '\n\n'])
        self.preformat = False
        
    def visit_paragraph(self, node):
        self.output.append(self.indent)
        
    def depart_paragraph(self, node):
        self.output.append('\n\n')
        if self.indent == self.list_item_prefix:
            # we're in a sub paragraph of a list item
            self.indent = ' ' * self.list_depth
        
    def visit_reference(self, node):
        if node.has_key('refuri'):
            href = node['refuri']
        elif node.has_key('refid'):
            href = '#' + node['refid']
        else:
            href = None
        self.output.append('[' + href + ' ')

    def depart_reference(self, node):
        self.output.append(']')

    def visit_subtitle(self, node):
        self.output.append('=== ')

    def depart_subtitle(self, node):
        self.output.append(' ===\n\n')
        self.list_depth = 0
        self.indent = ''
        
    def visit_title(self, node):
        self.output.append('== ')

    def depart_title(self, node):
        self.output.append(' ==\n\n')
        self.list_depth = 0
        self.indent = ''
        
    def visit_title_reference(self, node):
        self.output.append("`")

    def depart_title_reference(self, node):
        self.output.append("`")

    def visit_emphasis(self, node):
        self.output.append('*')

    def depart_emphasis(self, node):
        self.output.append('*')
        
    def visit_literal(self, node):
        self.output.append('`')
        
    def depart_literal(self, node):
        self.output.append('`')


def runcmd(cmd):
    print cmd
    (status,output) = getstatusoutput(cmd)
    if status != success:
        raise Exception(output)


def section(doc, name):
    m = re.search(r'(%s\n%s.*?)\n[^\n-]{3,}\n-{3,}\n' %
                  (name, '-' * len(name)), doc, re.DOTALL)
    if m:
        return m.groups()[0]
    raise Exception('Section %s not found' % name)


def wikirst(doc):
    return publish_string(doc, writer=WikiWriter())


def plugin_interface():
    """use pudge browser to generate interface docs
    from nose.plugins.base.PluginInterface
    """
    b = pudge.browser.Browser(['nose.plugins.base'], None)
    m = b.modules()[0]
    intf = list([ c for c in m.classes() if c.name ==
                  'IPluginInterface'])[0]
    doc = wikirst(intf.doc())
    methods = [ m for m in intf.routines() if not m.name.startswith('_') ]
    methods.sort(lambda a, b: cmp(a.name, b.name))
    mdoc = []
    for m in methods:
        mdoc.append('*%s%s*\n\n' %  (m.name, m.formatargs()))
        mdoc.append(' ' + m.doc().replace('\n', '\n '))
        mdoc.append('\n\n')
    doc = doc + ''.join(mdoc)
    return doc


def example_plugin():
    # FIXME dump whole example plugin code from setup.py and plug.py
    # into python source sections
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        '..'))
    exp = os.path.join(root, 'examples', 'plugin')
    setup = file(os.path.join(exp, 'setup.py'), 'r').read()
    plug = file(os.path.join(exp, 'plug.py'), 'r').read()

    wik = "*%s:*\n{{{\n%s\n}}}\n"
    return wik % ('setup.py', setup) + wik % ('plug.py', plug)


def mkwiki(path):
    #
    # Pages to publish and the docstring(s) to load for that page
    #

    pages = {  #'SandBox': wikirst(section(nose.__doc__, 'Writing tests'))
        'WritingTests': wikirst(section(nose.__doc__, 'Writing tests')),
        'NoseFeatures': wikirst(section(nose.__doc__, 'Features')),
        'WritingPlugins': wikirst(nose.plugins.__doc__),
        'PluginInterface': plugin_interface(),
        # FIXME finish example plugin doc... add some explanation
        'ExamplePlugin': example_plugin(),
        
        'NosetestsUsage': '\n{{{\n' +
        nose.configure(help=True).replace('mkwiki.py', 'nosetests') +
        '\n}}}\n'
        }

    current = os.getcwd()
    w = Wiki(path)
    for page, doc in pages.items():
        print "====== %s ======" % page
        w.update_docs(page, doc)
        print "====== %s ======" % page
    os.chdir(current)


class Wiki(object):
    doc_re = re.compile(r'(#.*\n\n)?(.*?)' + div, re.DOTALL)
    
    def __init__(self, path):
        self.path = path
        self.newpages = []
        os.chdir(path)
        runcmd('svn up')

    def filename(self, page):
        if not page.endswith('.wiki'):
            page = page + '.wiki'
        return page
        
    def get_page(self, page):
        try:
            fh = file(self.filename(page), 'r')
            content = fh.read()
            fh.close()
            return content
        except IOError:
            self.newpages.append(page)
            return ''

    def set_docs(self, page, page_src, docs):
        wikified = docs + div
        if not page_src:
            new_src = wikified + warning
            print "! Adding new page"
        else:
            m = self.doc_re.search(page_src)
            if m:
                print "! Updating doc section"
                new_src = self.doc_re.sub(wikified, page_src, 1)
                # Restore any headers (lines marked by # at start of file)
                if m.groups()[0] is not None:
                    new_src = ''.join([m.groups()[0], new_src])
            else:
                print "! Adding new doc section"
                new_src = wikified + page_src
        if new_src == page_src:
            print "! No changes"
            return
        fh = file(self.filename(page), 'w')
        fh.write(new_src)
        fh.close()
        
    def update_docs(self, page, doc):
        current = self.get_page(page)
        self.set_docs(page, current, doc)
        if page in self.newpages:
            runcmd('svn add %s' % self.filename(page))

        
def main():
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'wiki'))
    mkwiki(path)

    
if __name__ == '__main__':
    main()
