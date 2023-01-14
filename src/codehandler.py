import json
import os
import re
from dependencyhandler import DependencyHandler
from dependencyhandler import Dependency

class CodeHandler:
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
        try:
            for path, subdirs, files in os.walk(repositoryPath):
                for name in files:
                    if self.checkValidCodeExtension(name):
                        self.addCodeFilePath(os.path.join(path, name))

                    if self.checkValidDependency(name):
                        self.addDependencyFilePath(os.path.join(path, name))
        except Exception as e:
            print(e)
            
    def checkValidCodeExtension(self, name):
        fileExtension = name.split(".")[-1]
        validExtension = set(self.codeFiles)
        return True if (fileExtension in validExtension) else False

    def checkValidDependency(self, name):
        validDependency = set(self.dependencyFiles)
        return True if (name in validDependency) else False
    
    def readFile(self, filePath):
        with open(filePath) as file:
            sourceFile = file.read()
        
        return sourceFile

    # get all dependencies from files
    def getDependencies(self, dependencyHandler):
        filesPath = self.getDependencyFilesPath()
        with open("rules/dependency.json", 'r') as file:
            dependencyRules = json.load(file)

        for filePath in filesPath:
            fileName = filePath.split("/")[-1]
            try:
                rules = dependencyRules[fileName]
                content = self.readFile(filePath)
                ecosystem = rules["ecosystem"]
                pattern= rules["pattern"]
                patternType = rules["pattern"]["type"]
                if patternType == "regex":
                    for expression in rules["pattern"]["expression"]:
                        regexResult = (re.compile(expression).findall(content))
                        self.dependencyParser(regexResult, pattern, dependencyHandler, filePath, ecosystem)

                if patternType == "json":
                    dependencyDict = json.loads(content)
                    self.dependencyParser(dependencyDict[rules["pattern"]["expression"][0]], pattern, dependencyHandler, filePath, ecosystem)
                    
            except Exception as e:
                print(repr(e))

    def dependencyParser(self, dependencyList, pattern, dependencyHandler, filePath, ecosystem):
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

    # ast
    # tokenize