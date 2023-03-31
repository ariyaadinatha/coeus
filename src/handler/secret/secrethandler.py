from tree_sitter import Language, Parser
from utils.codehandler import Code, FileHandler
from utils.vulnhandler import Vulnerable
from utils.log import logger
from datetime import datetime
import difflib
import json
import re

class SecretDetection:
    def __init__(self):
        with open("rules/secret-wordlist.json", 'r') as file:
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

    def getNode(self, node, sourceCode):
        assigntmentNodeType = ["assignment", ""]
        listNodeType = ["argument_list"]
        # ASSIGNMENT NODE
        
        # ARRAY NODE

    def getDirectValueNode(self, node, sourceCode):
        varValueNode = node.children[-1]
        variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]

        varNameNode = node.children[0]
        variableName = sourceCode[varNameNode.start_byte:varNameNode.end_byte]
        
        return variableValue, varValueNode.start_point[0]+1, variableName

    def getNestedValueNode(self, node, sourceCode):
        # ignoreValue = ["(", ")", ","]
        ignoreValue = []
        valueList = []

        for i in range(len(node.children)):
            varValueNode = node.children[i]
            variableValue = sourceCode[varValueNode.start_byte:varValueNode.end_byte]
            if variableValue not in ignoreValue:
                valueList.append(variableValue)

        return valueList, varValueNode.start_point[0]+1, functionName

    def checkWhiteList(self, variableName, variableValue, codePath):
        with open("rules/secret-whitelist.json", 'r') as file:
            whiteList = json.load(file)["whitelist"]

        if codePath not in whiteList:
            return 0

        if variableName not in whiteList[codePath]:
            return 0

        if variableValue not in whiteList[codePath][variableName]:
            return 0

        return 1

    def apostropheCleaner(self, variableValue):
        return variableValue[1:-1] if (variableValue[0] == '"' and variableValue[-1] == '"') else variableValue

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

    # secret detection algorithm
    def valueDetection(self, sourceCode, vulnHandler, codePath):
        # valueNode = ["assignment", "variable_declarator", "assignment_expression"]
        # functionNode = ["call", "method_invocation", "call_expression", "function_call_expression"]
        multipleNode = ["argument_list", "array", "arguments", "array_creation_expression", "list", "method_invocation"]
        for node in self.getAssignmentList():
            excludedContent = ["[", "]", "(", ")", ","]
            if node.children[-1].type == "object_creation_expression":
                continue

            if (node.children[-1].type in multipleNode):
                variableNameNode = node.children[0]
                variableName = sourceCode[variableNameNode.start_byte:variableNameNode.end_byte]
                variableType = node.children[-1].type

                for i in range (len(node.children[-1].children)):
                    variableValueNode = node.children[-1].children[i]
                    variableValue = sourceCode[variableValueNode.start_byte:variableValueNode.end_byte]
                    variableLine = variableValueNode.start_point[0]+1

                    if variableValue not in excludedContent:
                        confidenceLevel = 0
                        # print(variableValue)
                        cleanVariable = self.apostropheCleaner(variableValue)
                        if self.checkWhiteList(variableName, cleanVariable, codePath):
                            continue
                        
                        # REGEX DETECTION
                        if self.scanSecretVariable(cleanVariable):
                            confidenceLevel += 1

                        # SIMILARITY DETECTION
                        if self.similarityDetection(variableName):
                            confidenceLevel += 2

                        if confidenceLevel > 0:
                            confidence = None
                            if confidenceLevel == 1:
                                confidence = "Low"
                            if confidenceLevel == 2:
                                confidence = "Medium"
                            if confidenceLevel == 3:
                                confidence = "High"

                            vuln = Vulnerable("Use of Hardcoded Credentials", 
                                    "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                                    "CWE-798", "High", confidence, {variableName: cleanVariable}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                            vulnHandler.addVulnerable(vuln)

            else:
                variableValue, variableLine, variableName = self.getDirectValueNode(node, sourceCode)
                cleanVariable = self.apostropheCleaner(variableValue)
                confidenceLevel = 0

                # skip variable if found on whitelist
                if self.checkWhiteList(variableName, cleanVariable, codePath):
                    continue

                # REGEX DETECTION
                if self.scanSecretVariable(cleanVariable):
                    confidenceLevel += 1

                # SIMILARITY DETECTION
                if self.similarityDetection(variableName):
                    confidenceLevel += 2

                if confidenceLevel > 0:
                    confidence = None
                    if confidenceLevel == 1:
                        confidence = "Low"
                    if confidenceLevel == 2:
                        confidence = "Medium"
                    if confidenceLevel == 3:
                        confidence = "High"
                
                    vuln = Vulnerable("Use of Hardcoded Credentials", 
                        "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                        "CWE-798", "High", confidence, {variableName: cleanVariable}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                    vulnHandler.addVulnerable(vuln)


    # Regex based detection
    def scanSecretVariable(self, variableValue):
        with open("rules/secret-regex.json", 'r') as file:
            regex = json.load(file)

        regexPattern = [re.compile(x) for x in regex["pattern"]]
        excludedPattern = [re.compile(x) for x in regex["exclussion"]]

        # find variable in excluded pattern
        for pattern in excludedPattern:
            if pattern.search(variableValue):
                return 0
                
        sus = 0
        for pattern in regexPattern:
            sus +=1 if pattern.search(variableValue) else 0

        return (sus > 2)

    def similarityDetection(self, variableName):
        threshold = 0.7

        similarities = [(word, difflib.SequenceMatcher(None, variableName, word).ratio()) for word in self.getSecretWordList()]
        maxSimilarity = max(similarities, key=lambda x: x[1])

        # if maxSimilarity[1] >= threshold:
        #     print(variableName, maxSimilarity[0], maxSimilarity[1])

        
        return maxSimilarity[1] >= threshold