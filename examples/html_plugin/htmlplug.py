"""This is a very basic example of a plugin that controls all test
output. In this case, it formats the output as ugly unstyled html.

Upgrading this plugin into one that uses a template and css to produce
nice-looking, easily-modifiable html output is left as an exercise for
the reader who would like to see his or her name in the nose AUTHORS file.
"""
import traceback
from nose.plugins import Plugin

class HtmlOutput(Plugin):
    """Output test results as ugly, unstyled html.
    """
    
    name = 'html-output'
    
    def __init__(self):
        super(HtmlOutput, self).__init__()
        self.html = [ '<html><head>',
                      '<title>Test output</title>',
                      '</head><body>' ]
    
    def addSuccess(self, test, capt):
        self.html.append('<span>ok</span>')
        
    def addSkip(self, test):
        self.html.append('<span>SKIPPED</span>')
        
    def addDeprecated(self, test):
        self.html.append('<span>DEPRECATED</span>')

    def addError(self, test, err, capt):
        err = self.formatErr(err)
        self.html.append('<span>ERROR</span>')
        self.html.append('<pre>%s</pre>' % err)
        if capt:
            self.html.append('<pre>%s</pre>' % capt)
            
    def addFailure(self, test, err, capt, tb_info):
        err = self.formatErr(err)
        self.html.append('<span>FAIL</span>')
        self.html.append('<pre>%s</pre>' % err)
        if tb_info:
            self.html.append('<pre>%s</pre>' % tb_info)
        if capt:
            self.html.append('<pre>%s</pre>' % capt)

    def finalize(self, result):
        self.html.append('<div>')
        self.html.append("Ran %d test%s" %
                         (result.testsRun, result.testsRun != 1 and "s" or ""))
        self.html.append('</div>')
        self.html.append('<div>')
        if not result.wasSuccessful():
            self.html.extend(['<span>FAILED ( ',
                              'failures=%d ' % len(result.failures),
                              'errors=%d' % len(result.errors),
                              ')</span>'])                             
        else:
            self.html.append('OK')
        self.html.append('</div></body></html>')
        # print >> sys.stderr, self.html
        for l in self.html:
            self.stream.writeln(l)

    def formatErr(self, err):
        exctype, value, tb = err
        return traceback.format_exception(exctype, value, tb)
    
    def setOutputStream(self, stream):
        # grab for own use
        self.stream = stream        
        # return dummy stream
        class dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
        d = dummy()
        return d
    
    def startTest(self, test):
        self.html.extend([ '<div><span>',
                           test.shortDescription() or str(test),
                           '</span>' ])
        
    def stopTest(self, test):
        self.html.append('</div>')
