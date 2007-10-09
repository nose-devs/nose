#!/usr/bin/env python

from commands import getstatusoutput
from docutils.core import publish_string, publish_parts
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader
from docutils.writers import Writer
from nose.config import Config
import nose.plugins
from nose.plugins.manager import BuiltinPluginManager
from nose.plugins import errorclass
import nose
import os
import pudge.browser
import re
import sys
import textwrap
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from mkdocs import formatargspec

# constants
success = 0
div = '\n----\n'
warning = """
*Do not edit above this line. Content above this line is automatically
generated and edits above this line will be discarded.*

= Comments =
"""
wiki_word_re = re.compile(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+')

def ucfirst(s):
    return s[0].upper() + s[1:].lower()

def words(s):
    return s.split(' ')


def is_wiki_word(text):
    return wiki_word_re.match(text)

        
def wiki_word(node):
    orig = text = node.astext()
    # handle module/plugin links -- link to code
    if is_wiki_word(text):
        node['refuri'] = text
    else:
        if '.' in text:
            parts = text.split('.')
            link = 'http://python-nose.googlecode.com/svn/trunk'
            for p in parts:
                # stop at class names
                if p[0].upper() == p[0]:
                    break
                link += '/' + p        
            node['refuri'] = link
            return True
        node['refuri'] = ''.join(map(ucfirst, words(text)))
    print "Unknown ref %s -> %s" % (orig, node['refuri'])
    del node['refname']
    node.resolved = True
    return True
wiki_word.priority = 100

class WWReader(Reader):
    unknown_reference_resolvers = (wiki_word,)

    
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

    def visit_doctest_block(self, node):
        self.output.extend(['{{{', '\n'])
        self.preformat = True

    def depart_doctest_block(self, node):
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
    return publish_string(doc, reader=WWReader(), writer=WikiWriter())


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
        # FIXME fix the arg list so literal os.environ is not in there
        mdoc.append('*%s%s*\n\n' %  (m.name, formatargspec(m.obj)))
        # FIXME this is resulting in poorly formatted doc sections
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


def tools():
    top = wikirst(nose.tools.__doc__)
    b = pudge.browser.Browser(['nose.tools'], None)
    m = b.modules()[0]
    funcs = [ (f.name, f.formatargs().replace('(self, ', '('), f.doc())
              for f in m.routines() ]
    funcs.sort()
    mdoc = [top, '\n\n']
    for name, args, doc in funcs:
        mdoc.append("*%s%s*\n\n" % (name, args))
        mdoc.append(' ' + doc.replace('\n', '\n '))
        mdoc.append('\n\n')
    return ''.join(mdoc)


def usage():
    conf = Config(plugins=BuiltinPluginManager())
    usage_text = conf.help(nose.main.__doc__).replace('mkwiki.py', 'nosetests')
    out = '{{{\n%s\n}}}\n' % usage_text
    return out


def mkwiki(path):
    #
    # Pages to publish and the docstring(s) to load for that page
    #

    pages = {  #'SandBox': wikirst(section(nose.__doc__, 'Writing tests'))
        'WritingTests': wikirst(section(nose.__doc__, 'Writing tests')),
        'NoseFeatures': wikirst(section(nose.__doc__, 'Features')),
        'WritingPlugins': wikirst(nose.plugins.__doc__),
        'PluginInterface': plugin_interface(),
        'ErrorClassPlugin': wikirst(errorclass.__doc__),
        'TestingTools': tools(),
        'FindingAndRunningTests': wikirst(
            section(nose.__doc__, 'Finding and running tests')),
        # FIXME finish example plugin doc... add some explanation
        'ExamplePlugin': example_plugin(),
        
        'NosetestsUsage': usage(),
        }

    current = os.getcwd()
    w = Wiki(path)
    for page, doc in pages.items():
        print "====== %s ======" % page
        w.update_docs(page, doc)
        print "====== %s ======" % page
    os.chdir(current)


class Wiki(object):
    doc_re = re.compile(r'(.*?)' + div, re.DOTALL)
    
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
        headers = []
        content = []

        try:
            fh = file(self.filename(page), 'r')
            in_header = True
            for line in fh:
                if in_header:
                    if line.startswith('#'):
                        headers.append(line)
                    else:
                        in_header = False
                        content.append(line)
                else:
                    content.append(line)
            fh.close()            
            return (headers, ''.join(content))
        except IOError:
            self.newpages.append(page)
            return ('', '')

    def set_docs(self, page, headers, page_src, docs):
        wikified = docs + div
        if not page_src:
            new_src = wikified + warning
            print "! Adding new page"
        else:
            m = self.doc_re.search(page_src)
            if m:
                print "! Updating doc section"
                new_src = self.doc_re.sub(wikified, page_src, 1)
            else:
                print "! Adding new doc section"
                new_src = wikified + page_src
        if new_src == page_src:
            print "! No changes"
            return        
        # Restore any headers (lines marked by # at start of file)
        if headers:
            new_src = ''.join(headers) + '\n' + new_src
        fh = file(self.filename(page), 'w')
        fh.write(new_src)
        fh.close()
        
    def update_docs(self, page, doc):
        headers, current = self.get_page(page)
        self.set_docs(page, headers, current, doc)
        if page in self.newpages:
            runcmd('svn add %s' % self.filename(page))

            
def findwiki(root):
    if not root or root is '/': # not likely to work on windows
        raise ValueError("wiki path not found")
    if not os.path.isdir(root):
        return findwiki(os.path.dirname(root))
    entries = os.listdir(root)
    if 'wiki' in entries:
        return os.path.join(root, 'wiki')
    return findwiki(os.path.dirname(root))


def main():
    path = findwiki(os.path.abspath(__file__))
    mkwiki(path)

    
if __name__ == '__main__':
    main()
