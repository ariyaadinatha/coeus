import json
import os
import re
from handler.dependency.dependencyhandler import Dependency
from utils.log import logger
from tree_sitter import Language, Parser, Node
from typing import Callable
import csv
import uuid
import xmltodict

import traceback


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
        print("Searching all relevant files")
        print(repositoryPath)
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
        try:
            with open(filePath, 'r', encoding="utf-8") as file:
                sourceFile = file.read()
        
            return sourceFile
        except:
            logger.error(f"Readfile error : {repr(e)}, param: {codePath}")

    # get all dependencies from files
    def getDependencies(self, dependencyHandler, mode):
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
                        self.dependencyParser(regexResult, pattern, dependencyHandler, filePath, ecosystem, mode)
                    logger.info(f"Completed pattern matching for {fileName}")

                if patternType == "json":
                    logger.info(f"Matching {patternType} pattern...")
                    if fileName == "pom.xml":
                        try:
                            pomDict = xmltodict.parse(content)["project"]

                            with open(f"java-dependency.json", "w") as fileRes:
                                fileRes.write(json.dumps(pomDict, indent=4))

                            javaDependencyDict = pomDict["dependencyManagement"]["dependencies"]["dependency"]
                            dependencyDict = {"dependencies": []}

                            for dependency in javaDependencyDict:
                                # print(len(javaDependencyDict))
                                dependencyPOMName = f'{dependency["groupId"]}:{dependency["artifactId"]}'
                                versionPOM = dependency["version"]
                                # print(f"deppomname: {dependencyPOMName}")
                                # print(f"versionpom: {versionPOM}")
                                    
                                if versionPOM[0] == "$":
                                    try:
                                        getVersionName = f'{dependency["artifactId"]}.version'
                                        # print(f"getversionname: {getVersionName}")
                                        versionPOM = pomDict["properties"][getVersionName]
                                    except:
                                        getVersionName = versionPOM[2:-1]
                                        # print(f"getversionname except: {getVersionName}")
                                        versionPOM = pomDict["properties"][getVersionName]

                                    # print(versionPOM)

                                betterDict = {
                                    "name": dependencyPOMName,
                                    "version": versionPOM
                                }

                                dependencyDict["dependencies"].append(betterDict)
                            # print(dependencyDict)
                        except Exception as e:
                            logger.error(f"Error: {repr(e)}")
                            # tb = traceback.format_exc()
                            # logger.error(f"Error: {repr(e)}\n{tb}")

                    else:
                        dependencyDict = json.loads(content)
                    
                    dependencyList = (dependencyDict[rules["pattern"]["expression"][0]])
                    self.dependencyParser(dependencyList, pattern, dependencyHandler, filePath, ecosystem, mode)
                    logger.info(f"Completed pattern matching for {fileName}")
                    
            except Exception as e:
                logger.error(f"Error : {repr(e)}")
                # tb = traceback.format_exc()
                # logger.error(f"Error: {repr(e)}\n{tb}")

    def dependencyParser(self, dependencyList, pattern, dependencyHandler, filePath, ecosystem, mode):
        logger.info("Parsing dependencies...")
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

                        required = values.get("requires")
                        if required:
                            for reqName, reqVer in required.items():
                                symbolList = ["^", "~", "<", ">", "="]

                                # without exact version
                                if any(c in reqVer for c in ["^", "~", "<", ">", "="]) and mode != "high":
                                    continue

                                parsedVer = reqVer.replace("^", "").replace("~", "").replace(">", "").replace("<", "").replace("=", "").replace(" ", "")
                                dep = Dependency(reqName, parsedVer, ecosystem, filePath)
                                dependencyHandler.addDependency(dep)

        
        except Exception as e:
            logger.error(f"Error : {repr(e)}")

class CodeProcessor:
    def __init__(self, language, sourceCode):
        Language.build_library(
          # Store the library in the `build` directory
          'build/my-languages.so',
          # Include one or more languages
          [
            'vendor/tree-sitter-java',
            'vendor/tree-sitter-php',
            'vendor/tree-sitter-javascript',
            'vendor/tree-sitter-python',
          ]
            # 'vendor/tree-sitter-typescript/typescript'
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
        
        print(f'{indent}[{node.id}] {node.type} - is_named?{node.is_named} : {node.text.decode("utf-8") }')

        tree.append((node.type, node.text.decode("utf-8")))

        for child in node.children:
            self.traverseTree(child, tree, depth + 2)

    def createTreeListWithId(self, node: Node, tree: list[tuple], parentId: str, rootId: str = "default", statement_order: int = 0, depth=0):
        removedList = ['"', '=', '(', ')', '[', ']', ':']
        indent = ' ' * depth
        if node.type in removedList:
            return
        
        print(f'{indent}[{node.id}] {node.type}: {node.text.decode("utf-8") }')

        nodeId = uuid.uuid4().hex

        # track statement order
        if (rootId == "default"):
            rootId = nodeId

        # add node information to tree
        if parentId == rootId:
            tree.append((nodeId, node.type, node.text.decode("utf-8"), parentId, statement_order))
        else:
            tree.append((nodeId, node.type, node.text.decode("utf-8"), parentId, 0))

        # iterate through children
        for index, child in enumerate(node.children, start = 1):
            if parentId == rootId:
                print(child.text.decode("utf-8"))
            self.createTreeListWithId(
                node = child,
                tree = tree,
                parentId = nodeId,
                rootId = rootId,
                statement_order = statement_order + index,
                depth = depth + 2)

    def convertNodeToCSVRow(self, node: Node) -> tuple:
        return (node.id, node.type, node.text.decode("utf-8"), node.parent.id)

    def exportToCSV(self):
        header = ['id', 'type', 'content', 'parent_id', 'statement_order']
        with open(f'./csv/{uuid.uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for node in self.treeList:
                row = [attr for attr in node]
                writer.writerow(row)

    def searchTree(self, node, keyword, result):
        try:
            if node.type == keyword:
                result.append(node)
            for child in node.children:
                self.searchTree(child, keyword, result)
        except Exception as e:
            logger.error(f"Search tree error : {repr(e)}, param: {keyword, node}")

    def getNodes(self, node, keyword, result):
        if node.type == keyword:
            varNameNode = node.children[0]
            variableName = self.getSourceCode()[varNameNode.start_byte:varNameNode.end_byte]
            varValueNode = node.children[-1]
            variableValue = self.getSourceCode()[varValueNode.start_byte:varValueNode.end_byte]
            result.append({variableName: variableValue})
        for child in node.children:
            self.getNodes(child, keyword, result)