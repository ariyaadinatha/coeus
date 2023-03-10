import json
import os
import re
from handler.dependency.dependencyhandler import Dependency
from utils.log import logger
from tree_sitter import Language, Parser, Node
from typing import Callable
import csv
import uuid

class FileHandler:
    def __init__(self):
        self.codeFilesPath = []
        self.dependencyFilesPath = []
        # load file configuration
        with open("config/files.json") as file:
            fileConfig = json.load(file)
        self.dependencyFiles = fileConfig["importantFiles"]["dependencyFile"]
        self.codeFiles = fileConfig["importantFiles"]["sourceCode"]

    def addCodeFile(self, file):
        self.codeFiles.append(file)

    def addDependencyFile(self, file):
        self.dependencyFiles.append(file)

    def addCodeFilePath(self, path):
        self.codeFilesPath.append(path)

    def addDependencyFilePath(self, path):
        self.dependencyFilesPath.append(path)

    def getCodeFilesPath(self):
        return self.codeFilesPath

    def getDependencyFilesPath(self):
        return self.dependencyFilesPath

    # get all relevant files from a project
    def getAllFilesFromRepository(self, repositoryPath):
        logger.info("Searching all relevant files")
        try:
            for path, subdirs, files in os.walk(repositoryPath):
                for name in files:
                    if self.checkValidCodeExtension(name):
                        self.addCodeFilePath(os.path.join(path, name))

                    if self.checkValidDependency(name):
                        self.addDependencyFilePath(os.path.join(path, name))
        except Exception as e:
            logger.error(f"Error : {e}")
            
    def checkValidCodeExtension(self, name):
        fileExtension = name.split(".")[-1]
        validExtension = set(self.codeFiles)
        return (fileExtension in validExtension)

    def checkValidDependency(self, name):
        validDependency = set(self.dependencyFiles)
        return (name in validDependency)
    
    def readFile(self, filePath):
        with open(filePath) as file:
            sourceFile = file.read()
        
        return sourceFile

    # get all dependencies from files
    def getDependencies(self, dependencyHandler):
        logger.info("Searching dependencies...")
        filesPath = self.getDependencyFilesPath()
        with open("rules/dependency.json", 'r') as file:
            dependencyRules = json.load(file)

        for filePath in filesPath:
            fileName = filePath.split("/")[-1]
            try:
                logger.info(f"Found {fileName}")
                rules = dependencyRules[fileName]
                content = self.readFile(filePath)
                ecosystem = rules["ecosystem"]
                pattern= rules["pattern"]
                patternType = rules["pattern"]["type"]
                if patternType == "regex":
                    logger.info(f"Matching {patternType} pattern...")
                    for expression in rules["pattern"]["expression"]:
                        regexResult = (re.compile(expression).findall(content))
                        self.dependencyParser(regexResult, pattern, dependencyHandler, filePath, ecosystem)
                    logger.info(f"Completed pattern matching for {fileName}")

                if patternType == "json":
                    logger.info(f"Matching {patternType} pattern...")
                    dependencyDict = json.loads(content)
                    self.dependencyParser(dependencyDict[rules["pattern"]["expression"][0]], pattern, dependencyHandler, filePath, ecosystem)
                    logger.info(f"Completed pattern matching for {fileName}")
                    
            except Exception as e:
                logger.error(f"Error : {repr(e)}")

    def dependencyParser(self, dependencyList, pattern, dependencyHandler, filePath, ecosystem):
        try:
            patternType = pattern["type"]
            if patternType == "regex":
                for dependency in dependencyList:
                    parsedDep = dependency.split("==")
                    dep = Dependency(parsedDep[0], parsedDep[1], ecosystem, filePath)
                    dependencyHandler.addDependency(dep)

            if patternType == "json":
                patternEnumerate = pattern["enumerate"]
                if patternEnumerate == "list":
                    for dep in dependencyList:
                        dep = Dependency(dep[pattern["keyName"]], dep[pattern["versionName"]], ecosystem, filePath)
                        dependencyHandler.addDependency(dep)

                if patternEnumerate == "dict":
                    for key, values in dependencyList.items():
                        dep = Dependency(key, values[pattern["versionName"]], ecosystem, filePath)
                        dependencyHandler.addDependency(dep)
        
        except Exception as e:
            logger.error(f"Error : {repr(e)}")



class Code:
    def __init__(self, language, sourceCode):
        Language.build_library(
          # Store the library in the `build` directory
          'build/my-languages.so',
          # Include one or more languages
          [
            'vendor/tree-sitter-java',
            'vendor/tree-sitter-php',
            'vendor/tree-sitter-javascript',
            'vendor/tree-sitter-python'
          ]
        )
        self.language = Language('build/my-languages.so', language)
        self.sourceCode = sourceCode
        self.parser = Parser()
        self.parser.set_language(self.language)
        self.tree = self.parser.parse(bytes(self.getSourceCode(), "utf8"))
        self.rootNode = self.tree.root_node
        self.treeList = []

    def getSourceCode(self):
        return self.sourceCode

    def getRootNode(self):
        return self.rootNode

    def getTree(self):
        return self.tree
    
    def getTreeList(self):
        if self.treeList == []:
            self.createTreeListWithId(self.getRootNode, self.treeList, 'root')
            
        return self.treeList

    def parseLanguage(self):
        return self.rootNode.sexp()

    def traverseTree(self, node: Node, tree: list[tuple], depth=0):
        removedList = ['"', '=', '(', ')', '[', ']', ':']
        indent = ' ' * depth
        if node.type in removedList:
            return
        
        print(f'{indent}[{node.id}] {node.type}: {node.text.decode("utf-8") }')

        tree.append((node.type, node.text.decode("utf-8")))

        for child in node.children:
            self.traverseTree(child, tree, depth + 2)

    def createTreeListWithId(self, node: Node, tree: list[tuple], parentId: str, depth=0):
        removedList = ['"', '=', '(', ')', '[', ']', ':']
        indent = ' ' * depth
        if node.type in removedList:
            return
        
        print(f'{indent}[{node.id}] {node.type}: {node.text.decode("utf-8") }')

        nodeId = uuid.uuid4().hex

        tree.append((nodeId, node.type, node.text.decode("utf-8"), parentId))

        for child in node.children:
            self.createTreeListWithId(child, tree, nodeId, depth + 2)

    def convertNodeToCSVRow(self, node: Node) -> tuple:
        return (node.id, node.type, node.text.decode("utf-8"), node.parent.id)

    def exportToCSV(self):
        header = ['id', 'type', 'content', 'parent_id']
        with open(f'./csv/{uuid.uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for node in self.treeList:
                row = [attr for attr in node]
                writer.writerow(row)

    def searchTree(self, node, keyword, result):
        if node.type == keyword:
            result.append(node)
        for child in node.children:
            self.searchTree(child, keyword, result)

    def getNodes(self, node, keyword, result):
        if node.type == keyword:
            varNameNode = node.children[0]
            variableName = self.getSourceCode()[varNameNode.start_byte:varNameNode.end_byte]
            varValueNode = node.children[-1]
            variableValue = self.getSourceCode()[varValueNode.start_byte:varValueNode.end_byte]
            result.append({variableName: variableValue})
        for child in node.children:
            self.getNodes(child, keyword, result)