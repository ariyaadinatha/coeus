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
        # PYTHON
        if (node.type == "assignment"):
            varValueNode = node.children[-1]
            variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]

            return variableValue, varValueNode.start_point[0]+1

        if (node.type == "argument_list"):
            ignoreValue = ["(", ")", ","]
            valueList = []
            for i in range(len(node.children)):
                varValueNode = node.children[i]
                variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]
                # print(variableValue)
                if variableValue not in ignoreValue:
                    valueList.append(variableValue)

            return valueList, varValueNode.start_point[0]+1

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
    def valueDetection(self, sourceCode, vulnHandler, codePath):
        for node in self.getAssignmentList():
            variableValue, variableLine = self.getNodeValue(node, sourceCode)
            if (node.type == "argument_list"):
                for value in variableValue:
                    self.scanSusVariable(value, variableLine)

            if (node.type == "assignment"):
                self.scanSusVariable(variableValue, variableLine)

    def scanSusVariable(self, variableValue, variableLine):
        regexPattern = [
            re.compile(".{9,}"),
            re.compile("(?=.*[a-z])(?=.*[A-Z]).+"),
            re.compile("(?=.*\d).+"),
            re.compile("(?=.*[@#$%^&+=]).+")
        ]

        sus = 0
        for pattern in regexPattern:
            sus +=1 if pattern.search(variableValue) else 0

        if (sus > 2):
            print(f"SUS VARIABLE: {variableValue}, LINE: {variableLine}")
            return 1
        else:
            return 0

    ### END OF SECRET DETECTION ALGORITHM ###