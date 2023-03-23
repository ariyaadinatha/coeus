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
        with open("rules/whitelist.json", 'r') as file:
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

    # detecting value using regex
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

#                 print(f"""
# var: {variableName}
# type: {variableType}
# len: {len(node.children[-1].children)}
# code: {codePath.split("/")[-1]}""")

                for i in range (len(node.children[-1].children)):
                    variableValueNode = node.children[-1].children[i]
                    variableValue = sourceCode[variableValueNode.start_byte:variableValueNode.end_byte]
                    variableLine = variableValueNode.start_point[0]+1

                    # # JAVA. should have created recursive, but ...
                    # if variableType == "object_creation_expression":
                    #     variableValueNode = node.children[-1].children[-1].children[i]
                    #     variableValue = sourceCode[variableValueNode.start_byte:variableValueNode.end_byte]
                    #     print("JAVA ", variableValue)


                    if variableValue not in excludedContent:
                        # print(variableValue)
                        cleanVariable = self.apostropheCleaner(variableValue)
                        if self.checkWhiteList(variableName, cleanVariable, codePath):
                            continue

                        if self.scanSecretVariable(cleanVariable):
                            vuln = Vulnerable("Use of Hardcoded Credentials", 
                                "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                                "CWE-798", "High", {variableName: cleanVariable}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                            vulnHandler.addVulnerable(vuln)

            else:
                # continue
                variableValue, variableLine, variableName = self.getDirectValueNode(node, sourceCode)
                cleanVariable = self.apostropheCleaner(variableValue)

                # skip variable if found on whitelist
                if self.checkWhiteList(variableName, cleanVariable, codePath):
                    continue

                if self.scanSecretVariable(cleanVariable):
                    vuln = Vulnerable("Use of Hardcoded Credentials", 
                        "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                        "CWE-798", "High", {variableName: cleanVariable}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                    vulnHandler.addVulnerable(vuln)

            # if len(node.children) > 1:   
            #     variableValue, variableLine, variableName = self.getDirectValueNode(node, sourceCode)
            #     print(f"ARR / FUNCT: {variableValue}")

            # if len(node.children) == 0:
            #     variableValue, variableLine, variableName = self.getDirectValueNode(node, sourceCode)
            #     print(f"VAR: {variableValue}")
            #     # print(type(variableValue))

            # list, array, arguments
            # if len(variableValue) > 1:
            #     functionArguments, functionLine, functionName = self.getNestedValueNode()
            #     for argument in functionArguments:
                    # if argument not in whitelist

            #         if self.scanSecretVariable(argument):
            #             print(f"SUS {argument}, name {variableName}, line {variableLine}")
                        # vuln = Vulnerable("Use of Hardcoded Credentials", 
                        # "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                        # "CWE-798", "High", {variableName: variableValue}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                        # vulnHandler.addVulnerable(vuln)

            # variableValue, variableLine, variableName = self.getNodeValue(node, sourceCode)
            # if (node.type == "argument_list" or node.children[-1].type == "list"):
            #     # print(variableValue)
            #     # print(node.children[-1].type)
            #     for value in variableValue:
            #         if self.scanSecretVariable(value, suspectedVariable):
            #             # print(f"BADUT MEMBERONTAK {suspectedVariable}")
            #             secretFound = True
            
            # TO DO ADD ANOTHER EXTENSION
            # if (node.type == "assignment"):
            #     if (node.children[-1].type == "list"):
            #         pass
            #     # if self.scanSecretVariable(variableValue, suspectedVariable):
            #     #     # print(f"BADUT MEMBERONTAK {suspectedVariable}")
            #     #     secretFound = True

            # if secretFound == True:
            #     # print("FOUND : ", variableValue, variableLine, variableName)
            #     vuln = Vulnerable("Use of Hardcoded Credentials", 
            #     "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
            #     "CWE-798", "High", {variableName: variableValue}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
            #     vulnHandler.addVulnerable(vuln)
            #     self.checkWhiteList(variableName, suspectedVariable, codePath)


    # detecting value using regex
    def valueDetectionOld(self, sourceCode, vulnHandler, codePath):
        valueNode = ["assignment", "variable_declarator", "assignment_expression"]
        functionNode = ["call", "method_invocation", "call_expression", "function_call_expression"]
        for node in self.getAssignmentList():
            secretFound = False
            variableValue, variableLine, variableName = self.getNodeValue(node, sourceCode)
            suspectedVariable = ""
            if (node.type == "argument_list" or node.children[-1].type == "list"):
                # print(variableValue)
                # print(node.children[-1].type)
                for value in variableValue:
                    if self.scanSecretVariable(value, suspectedVariable):
                        # print(f"BADUT MEMBERONTAK {suspectedVariable}")
                        secretFound = True
            
            # TO DO ADD ANOTHER EXTENSION
            if (node.type == "assignment"):

                if (node.children[-1].type == "list"):
                    pass
                # if self.scanSecretVariable(variableValue, suspectedVariable):
                #     # print(f"BADUT MEMBERONTAK {suspectedVariable}")
                #     secretFound = True

            if secretFound == True:
                # print("FOUND : ", variableValue, variableLine, variableName)
                vuln = Vulnerable("Use of Hardcoded Credentials", 
                "contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
                "CWE-798", "High", {variableName: variableValue}, codePath, variableLine, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                vulnHandler.addVulnerable(vuln)
                self.checkWhiteList(variableName, suspectedVariable, codePath)


    def scanSecretVariable(self, variableValue):
        regexPattern = [
            re.compile(".{9,}"),
            re.compile("(?=.*[a-z])(?=.*[A-Z]).+"),
            re.compile("(?=.*\d).+"),
            re.compile("(?=.*[@#$%^&+=]).+")
        ]

        sus = 0
        # print(f"scan var {variableValue}")
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