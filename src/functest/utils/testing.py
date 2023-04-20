import unittest

from utils.codehandler import FileHandler, CodeProcessor
from utils.vulnhandler import Vulnerable, VulnerableHandler

class TestFileHandler(unittest.TestCase):
    def setUp(self):
        pass

class TestCodeProcessor(unittest.TestCase):
    def setUp(self):
        self.code = """
        print("hello everynyan")
        how = "are you?"
        fine = "zhank u" """
        self.codeProcessor = CodeProcessor("python", self.code)
    
    def test_code_processor_source_code_get(self):
        # self.codeProcessor.getSourceCode()
        pass

    def test_code_processor_root_node_get(self):
        # self.codeProcessor.getRootNode()
        pass

    def test_code_processor_traverse_tree(self):
        pass

    def test_code_processor_search_tree(self):
        pass

    def test_code_processor_get_nodes(self):
        pass

class TestVulnerable(unittest.TestCase):
    def setUp(self):
        self.title = "title"
        self.details = "details"
        self.aliases = "aliases"
        self.severity = "severity"
        self.confidence = "confidence"
        self.evidence = "evidence"
        self.files = "files"
        self.line = "line"
        self.date = "date"
        self.vuln = Vulnerable(self.title, self.details, self.aliases, self.severity, self.confidence, self.evidence, self.files, self.line, self.date)

    def test_vulnerable_get_title(self):
        self.assertEqual(self.vuln.getTitle(), self.title)
    
    def test_vulnerable_get_details(self):
        self.assertEqual(self.vuln.getDetails(), self.details)
    
    def test_vulnerable_get_aliases(self):
        self.assertEqual(self.vuln.getAliases(), self.aliases)
        
    def test_vulnerable_get_severity(self):
        self.assertEqual(self.vuln.getSeverity(), self.severity)
    
    def test_vulnerable_get_evidence(self):
        self.assertEqual(self.vuln.getEvidence(), self.evidence)
    
    def test_vulnerable_get_files(self):
        self.assertEqual(self.vuln.getFiles(), self.files)
        
    def test_vulnerable_get_line(self):
        self.assertEqual(self.vuln.getLine(), self.line)
    
    def test_vulnerable_get_date(self):
        self.assertEqual(self.vuln.getDate(), self.date)

    def test_vulnerable_get_whitelist(self):
        self.assertEqual(self.vuln.getWhitelist(), False)

    def test_vulnerable_set_whitelist(self):
        self.vuln.setWhitelist()
        self.assertEqual(self.vuln.getWhitelist(), True)

class TestVulnerableHandler(unittest.TestCase):
    def setUp(self):
        self.vulnerableHandler = VulnerableHandler()
        self.vuln1 = Vulnerable("title1", "details1", "aliases1", "severity1", "confidence1", "evidence1", "files1", "line1", "date1")
        self.vuln2 = Vulnerable("title2", "details2", "aliases2", "severity2", "confidence2", "evidence2", "files2", "line2", "date2")

    def test_vulnerable_handler_getVulnerable(self):
        self.assertEqual(len(self.vulnerableHandler.getVulnerable()), 0)

    def test_vulnerable_handler_addVulnerable(self):
        self.vulnerableHandler.addVulnerable(self.vuln1)
        self.assertEqual(len(self.vulnerableHandler.getVulnerable()), 1)
        self.vulnerableHandler.addVulnerable(self.vuln1)
        self.assertEqual(len(self.vulnerableHandler.getVulnerable()), 2)

if __name__ == '__main__':
    unittest.main()