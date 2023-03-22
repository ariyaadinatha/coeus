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

            varNameNode = node.children[0]
            variableName = sourceCode[varNameNode.start_byte:varNameNode.end_byte]

            # print(variableValue)
            return variableValue.replace("'", "").replace('"', ''), varValueNode.start_point[0]+1, variableName

        if (node.type == "argument_list"):
            ignoreValue = ["(", ")", ","]
            valueList = []

            # DEBUG
            functionName = None
            parentNode = node.parent.parent.children[0]
            if (parentNode.type == "call"):
                parentChild = parentNode.children[0]
                functionName = sourceCode[parentChild.start_byte:parentChild.end_byte]
            for i in range(len(node.children)):
                varValueNode = node.children[i]
                variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]
                if variableValue not in ignoreValue:
                    valueList.append(variableValue)

            # print(variableValue)
            parsedValueList = [x.replace("'", '"').replace('"', '') for x in valueList]
            return parsedValueList, varValueNode.start_point[0]+1, functionName

    def checkWhiteList(self, variableName, variableValue, codePath):
        with open("rules/whitelist.json", 'r') as file:
            whiteList = json.load(file)["whitelist"]

        # print(f"\nvarName :{variableName}, varValue :{variableValue}")
        if codePath not in whiteList:
            return

        if variableName not in whiteList[codePath]:
            return
        # print(whiteList[codePath][variableName])

        if variableValue not in whiteList[codePath][variableName]:
            return

        print(f"WHITELISTED, NAME: {variableName}, VALUE: {variableValue}, PATH: {codePath}")

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

    # detecting value using regex
    def valueDetection(self, sourceCode, vulnHandler, codePath):
        for node in self.getAssignmentList():
            secretFound = False
            variableValue, variableLine, variableName = self.getNodeValue(node, sourceCode)
            suspectedVariable = ""
            if (node.type == "argument_list"):
                # print(variableValue)
                for value in variableValue:
                    if self.scanSusVariable(value, suspectedVariable):
                        # print(f"BADUT MEMBERONTAK {suspectedVariable}")
                        secretFound = True
            
            # TO DO ADD ANOTHER EXTENSION
            if (node.type == "assignment"):
                if self.scanSusVariable(variableValue, suspectedVariable):
                    # print(f"BADUT MEMBERONTAK {suspectedVariable}")

                    secretFound = True

            if secretFound == True:
                # print("FOUND : ", variableValue, variableLine, variableName)
                vuln = Vulnerable("Use of Hardcoded Credentials", 
                "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                "CWE-798", "High", {variableName: variableValue}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                vulnHandler.addVulnerable(vuln)
                self.checkWhiteList(variableName, suspectedVariable, codePath)


    def scanSusVariable(self, variableValue, suspectedVariable):
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
            suspectedVariable = variableValue
            # print(f"SUS: {suspectedVariable}")
            return 1
        else:
            return 0

    # TODO
    def complementaryScan():
        pass

    # TODO
    def similarityDetection(self):
        for node in self.getAssignmentList():
            variableName, variableValue = self.getNodeActualValue(node, sourceCode)

    ### END OF SECRET DETECTION ALGORITHM ###