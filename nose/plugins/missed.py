from nose.plugins.base import Plugin
from nose.util import split_test_name, test_address

class MissedTests(Plugin):
    """
    Enable to get a warning when tests specified on the command line
    are not found during the test run.
    """
    name = 'missed-tests'
    
    def begin(self):
        if not self.conf.tests:
            self.missed = None
        else:
            self.missed = self.conf.tests[:]
            
    def finalize(self, result):
        if self.missed:
            for missed in self.missed:
                result.stream.writeln("WARNING: missed test '%s'" % missed)
        
    def match(self, test, test_name):
        adr_file, adr_mod, adr_tst = test_address(test)
        chk_file, chk_mod, chk_tst = split_test_name(test_name)
        
        if chk_file is not None and not adr_file.startswith(chk_file):
            return False
        if chk_mod is not None and not adr_mod.startswith(chk_mod):
            return False
        if chk_tst is not None and chk_tst != adr_tst:
            # could be a test like Class.test and a check like Class
            if not '.' in chk_tst:
                try:
                    cls, mth = adr_tst.split('.')
                except ValueError:
                    return False
                if cls != chk_tst:            
                    return False
            else:
                return False
        return True

    def startTest(self, test):
        if not self.missed:
            return
        found = []
        for name in self.missed:
            if self.match(test, name):
                found.append(name)
        for name in found:
            self.missed.remove(name)
