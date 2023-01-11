import re
import requests

class Dependency:
    def __init__(self, name, version, ecosystem, fileLocation):
        self.name = name
        self.version = version
        self.ecosystem = ecosystem
        self.fileLocation = fileLocation

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getEcosystem(self):
        return self.ecosystem

    def getFileLocation(self):
        return self.fileLocation

    def getDependency(self):
        return self.__dict__

class VulnerableDependency(Dependency):
    def __init__(self, name, version, ecosystem, fileLocation, 
    details, aliases, severity=None, fixed=None):
        super().__init__(name, version, ecosystem, fileLocation)
        self.details = details
        self.aliases = aliases
        self.severity = severity
        self.fixed = fixed

    def getDetails(self):
        return self.details
    
    def getAliases(self):
        return self.aliases

    def getSeverity(self):
        return self.severity

    def getFixed(self):
        return self.fixed

class DependencyHandler:
    def __init__(self):
        self.dependencies = []
        self.vulnerableDependencies = []

    def getDependencies(self):
        return self.dependencies

    def getVulnerableDependencies(self):
        return self.vulnerableDependencies

    def addDependency(self, dependency):
        self.dependencies.append(dependency)

    def addVulnerableDependency(self, vulnDependendency):
        self.vulnerableDependencies.append(vulnDependendency)

    # scan dependency vulnerability
    def scanDependency(self, dependency: Dependency):
        url = "https://api.osv.dev/v1/query"
        obj = {
            "version": dependency.getVersion(),
            "package": {
                "name": dependency.getName(),
                "ecosystem": dependency.getEcosystem()
            }
        }

        result = requests.post(url, json=obj)
        return result.json()

    # scan all vulnerability
    def scanDependencies(self):
        for dependency in self.dependencies:
            result = self.scanDependency(dependency)
            if result:
                for vuln in result["vulns"]:
                    parsedRes = self.parseDependencyResult(vuln)
                    depObj = dependency.getDependency()
                    vulnDep = VulnerableDependency(
                        depObj["name"],
                        depObj["version"],
                        depObj["ecosystem"],
                        depObj["fileLocation"],
                        parsedRes["details"],
                        parsedRes["aliases"],
                        parsedRes["severity"],
                        parsedRes["fixed"]
                    )

                    self.addVulnerableDependency(vulnDep)

    # get important key from OSV response
    def parseDependencyResult(self, result):
        vulnResult = {}
        vulnResult["details"] = result.get("details")
        vulnResult["aliases"] = result.get("aliases")
        vulnResult["severity"] = result.get("severity")
        vulnResult["fixed"] = result.get("affected")[0].get("ranges")
    
        return vulnResult

    # get all dependencies used in a code
    def scanDependenciesUsingRegex(self, filePath):
        fileExtension = filePath.split(".")[-1]
        importList = []
        regexPattern = {
                "py": [ # python extension
                    re.compile('(?<=^import ).*'), # get words starting with import
                    re.compile('(?<=^from ).*?(?= import)') # get words between from and import
                ]
        }

        try:
            with open(filePath) as file:
                # enumerate each file
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
            print(repr(e))