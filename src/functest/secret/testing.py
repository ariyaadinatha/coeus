import unittest

from handler.secret.secrethandler import SecretDetection

class TestSecretDetection(unittest.TestCase):
    def setUp(self):
        self.variableValue1 = "tH1s_iS_P4ssW0rD"
        self.variableValue2 = "not a password"
        self.variableValue3 = '"hello"'
        self.variableName1 = "passworrd"
        self.variableName2 = "weather"
        self.secret = SecretDetection()

    def test_secret_assignment_get(self):
        pass

    def test_secret_assignment_add(self):
        pass

    def test_secret_assignment_clear(self):
        pass
    
    def test_secret_variable_node_get(self):
        pass

    def test_secret_direct_node_get(self):
        pass

    def test_secret_check_whitelist(self):
        self.assertEqual(self.secret.checkWhiteList("passwordTrue2", "waiwIASdij123", "testcase/basic/basic.js"), True)
        # self.assertEqual(self.secret.checkWhiteList("hello", "passw", "qwe"), True)

    def test_secret_apostrophe_cleaner(self):
        self.assertEqual(self.secret.apostropheCleaner(self.variableValue3), "hello")

    def test_secret_wordlist_detection(self):
        pass

    def test_secret_similarity_detection(self):
        self.assertEqual(self.secret.similarityDetection(self.variableName1), True)
        self.assertEqual(self.secret.similarityDetection(self.variableName2), False)

    def test_secret_regex_detection(self):
        self.assertEqual(self.secret.scanSecretVariable(self.variableValue1), True)
        self.assertEqual(self.secret.scanSecretVariable(self.variableValue2), False)

    def test_secret_value_detection(self):
        pass

if __name__ == '__main__':
    unittest.main()