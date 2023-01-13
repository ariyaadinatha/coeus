import json
import os
import re

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

    # get all dependencies
    def getDependencies(self):
        filesPath = self.getDependencyFilesPath()
        with open("rules/dependency.json", 'r') as file:
            dependencyRules = json.load(file)

        for filePath in filesPath:
            fileName = filePath.split("/")[-1]
            try:
                rules = dependencyRules[fileName]
                content = self.readFile(filePath)
                print(filePath)
                if rules["pattern"]["type"] == "regex":
                    for expression in rules["pattern"]["expression"]:
                        print(re.compile(expression).findall(content))
                        print(fileName)

                if rules["pattern"]["type"] == "json":
                    dependencyDict = json.loads(content)
                    for expression in rules["pattern"]["expression"]:
                        print(dependencyDict[expression])
                    
            except Exception as e:
                print(repr(e))

    # ast
    # tokenize