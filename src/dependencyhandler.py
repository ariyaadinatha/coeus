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
                    re.compile('(?<=^import ).*'), # get words starting with import
                    re.compile('(?<=^from ).*?(?= import)') # get words between from and import
                ]
        }

        importList = []

        try:
            with open(filePath) as file:
                # sourceFile = file.read()
                for lineNumber, line in enumerate(file, start=1):
                    for pattern in regexPattern[fileExtension]:
                        result = (pattern.search(line))
                        if result:
                            dependencyName = result.group(0)
                            print(f"{dependencyName} dependency found at line {lineNumber}")
                            importList.append(dependencyName)
            
            # remove duplicate item
            return list(set(importList))

        except Exception as e:
            pass
            # print(repr(e))