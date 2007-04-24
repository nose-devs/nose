#!/usr/bin/env python

import sys
from docutils.nodes import SparseNodeVisitor, paragraph, title_reference, \
    emphasis
from docutils.writers import Writer
from docutils.core import publish_string

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
        return '\n>>>\n\n'+ ''.join(self.output) + '\n\n<<<\n'

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
   
        
def main(source):
    output = publish_string(source, writer=WikiWriter())
    print output
    
if __name__ == '__main__':
    main(sys.stdin.read())
