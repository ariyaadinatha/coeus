import json
import os

class CodeHandler:
    def __init__(self):
        self.filesPath = []
        with open("config/files.json") as file:
            fileConfig = json.load(file)
        self.importantDependencyFiles = fileConfig["importantFiles"]["dependencyFile"]
        self.importantFilesList = fileConfig["importantFiles"]["sourceCode"]
        
    # get all relevant files from a project
    def getAllFilesFromRepository(self, repositoryPath):
        try:
            for path, subdirs, files in os.walk(repositoryPath):
                for name in files:
                    fileExtension = name.split(".")[-1]
                    if ((fileExtension in self.importantFilesList) or (fileExtension in self.importantDependencyFiles)):
                        self.filesPath.append(os.path.join(path, name))
        
        except Exception as e:
            print(e)
            
    def getImportantFiles(self):
        return self.filesPath

    def readFile(self, filePath):
        with open(filePath) as file:
            sourceFile = file.read()
        
        return sourceFile