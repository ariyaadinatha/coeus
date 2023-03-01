from tree_sitter import Language, Parser
from utils.codehandler import Code, FileHandler
from utils.vulnhandler import Vulnerable
from utils.log import logger
from datetime import datetime
import json
import re

class SecretDetection:
    def __init__(self):
        with open("rules/secret.json", 'r') as file:
            wordlist = json.load(file)["wordlist"]
        self.secretWordlist = wordlist
        self.assignmentList = []

    def getAssignmentList(self):
        return self.assignmentList

    def clearAssignmentList(self):
        self.assignmentList.clear()

    def getSecretWordList(self):
        return self.secretWordlist

    def addAssignment(self, assignmentDict):
        self.assignmentList.append(assignmentDict)

    def getNodeVariable(self, node, sourceCode):
        varNameNode = node.children[0]
        variableName = sourceCode[varNameNode.start_byte:varNameNode.end_byte]
        
        return variableName, varNameNode.start_point[0]+1
        
    def getNodeValue(self, node, sourceCode):
        varValueNode = node.children[-1]
        variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]
        
        return variableValue, variableValue.start_point[0]+1

    ### START OF SECRET DETECTION ALGORITHM ###
    def wordlistDetection(self, sourceCode, vulnHandler, codePath):
        for node in self.getAssignmentList():
            variableName, variableLine = self.getNodeVariable(node, sourceCode)
            if variableName in self.getSecretWordList():
                vuln = Vulnerable("Use of Hardcoded Credentials", 
                "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                "CWE-798", "High", variableName, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                # print(variableName, variableLine)
                vulnHandler.addVulnerable(vuln)
            

    def similarityDetection(self):
        for node in self.getAssignmentList():
            variableName, variableValue = self.getNodeActualValue(node, sourceCode)

    # detecting value using regex
    def valueDetection(self):
        for node in self.getAssignmentList():
            variableName, variableValue = self.getNodeActualValue(node, sourceCode)

    ### END OF SECRET DETECTION ALGORITHM ###
    

if __name__ == "__main__":
    sc = SecretDetection()
    sc.addAssignment("a")
    print(sc.getAssignmentList())
    sc.getAssignmentList().append("b")
    print(sc.getAssignmentList())
