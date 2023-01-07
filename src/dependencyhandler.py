import re

class Dependency:
    def __init__(self, name, version, fileLocation):
        self.name = name
        self.version = version
        self.fileLocation = fileLocation

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getFileLocation(self):
        return self.fileLocation

    def getDependency(self):
        return self.__dict__

class DependencyHandler:
    def __init__(self):
        self.dependencies = []
        # self.vulnerableDependencies = []

    def getDependencies(self):
        return self.dependencies

    def addDependencies(self, dependency):
        self.dependencies.append(dependency)

    # get all dependencies used in a code
    def scanDependencies(self, filePath):
        fileExtension = filePath.split(".")[-1]

        regexPattern = {
                "py": [ # python extension
                    re.compile('(?<=import ).*'), # get words starting with import
                    re.compile('(?<=from ).*?(?= import)') # get words between from and import
                ]
        }

        with open(filePath) as file:
            sourceFile = file.read()

        try:
            for pattern in regexPattern[fileExtension]:
                result = pattern.findall(sourceFile)
                print(result)
        except Exception as e:
            print(e)