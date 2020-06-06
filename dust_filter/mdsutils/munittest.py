"""munittest - unittest subclasses to allow for some prettier output

This file is useable as a drop-in replacemnt for unittest by doing:

import munittest as unittest
"""

import os.path
import unittest
from unittest import *

class TextTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super(TextTestResult, self).__init__(stream, descriptions, verbosity)
        if self.descriptions: self.indent = '  '
        else: self.indent = ''
        self.depth = 0
        self.width = 80

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return doc_first_line
        else:
            return str(test)

    def startSuite(self, suite):
        if self.showAll and self.descriptions:
            self.stream.write(self.indent * self.depth)
            try: desc = self.getDescription(suite)
            except AttributeError: desc = '(no description)'
            self.stream.writeln(desc)
        self.depth += 1
        
    def endSuite(self, suite):
        self.depth -= 1

    def startTest(self, test):
        if self.showAll:
            self.stream.write(self.indent * self.depth)
            d = self.getDescription(test)
            dwidth = self.width - len(self.indent) * self.depth - 11
            fmt = "%%-%is" % dwidth
            self.stream.write(fmt % d)
            self.stream.write(" ... ")

    def addSkip(self, test, reason):
        super(unittest.TextTestResult, self).addSkip(test, reason)
        if self.showAll:
            self.stream.writeln("skip")
            self.stream.write(self.indent * (self.depth + 1))
            self.stream.writeln('[ %s ]' % reason)
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()


class TestSuite(unittest.TestSuite):
    def shortDescription(self):
        return self.description
    
    def run(self, result):
        try: result.startSuite(self)
        except AttributeError: pass

        for test in self:
            if result.shouldStop:
                break
            test(result)

        try: result.endSuite(self)
        except AttributeError: pass

        return result

class TextTestRunner(unittest.TextTestRunner):
    resultclass = TextTestResult

class TestLoader(unittest.TestLoader):
    suiteClass = TestSuite

    def _get_doc_first_line(self, obj):
        doc = obj.__doc__
        if doc is not None:
            return doc.split('\n')[0]
        else:
            return obj.__name__

    def loadTestsFromModule(self, module, use_load_tests=True):
        tests = super(TestLoader, self).loadTestsFromModule(\
            module, use_load_tests)
        tests.description = self._get_doc_first_line(module)
        return tests

    def loadTestsFromTestCase(self, testCaseClass):
        tests = super(TestLoader, self).loadTestsFromTestCase(testCaseClass)
        tests.description = self._get_doc_first_line(testCaseClass)
        return tests
            
    def discover(self, start_dir, *args, **kwargs):
        tests = super(TestLoader, self).discover(start_dir, *args, **kwargs)
        tests.description = os.path.abspath(start_dir)
        return tests
