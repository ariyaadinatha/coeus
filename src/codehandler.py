import json
import os

class CodeHandler:
    def __init__(self):
        self.filesPath = []
        # load file configuration
        with open("config/files.json") as file:
            fileConfig = json.load(file)
        self.dependencyFiles = fileConfig["importantFiles"]["dependencyFile"]
        self.codeFiles = fileConfig["importantFiles"]["sourceCode"]

    def addCodeFile(self, file):
        self.codeFiles.append(file)

    def addDependencyFile(self, file):
        self.dependencyFiles.append(file)

    def addFilePath(self, path):
        self.filesPath.append(path)

    def readFile(self, source):
        with open(source, 'r') as file:
            content = file.read()
        return content

    def getImportantFiles(self):
        return self.filesPath

    # get all relevant files from a project
    def getAllFilesFromRepository(self, repositoryPath):
        try:
            for path, subdirs, files in os.walk(repositoryPath):
                for name in files:
                    if self.checkValidExtension(name):
                        self.addFilePath(os.path.join(path, name))
        except Exception as e:
            print(e)
            
    def checkValidExtension(self, name):
        fileExtension = name.split(".")[-1]
        validExtension = set(self.codeFiles).union(self.dependencyFiles)
        return True if (fileExtension in validExtension) else False
    
    def readFile(self, filePath):
        with open(filePath) as file:
            sourceFile = file.read()
        
        return sourceFile

    # get all dependencies
    def getDependencies(self):
        pass
    # ast
    # tokenize