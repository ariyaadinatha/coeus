import re
import requests
from utils.log import logger
from datetime import date
import json
import os

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
    details, aliases, severity=None, affected=None):
        super().__init__(name, version, ecosystem, fileLocation)
        self.details = details
        self.aliases = aliases
        self.severity = severity
        self.affected = affected

    def getDetails(self):
        return self.details
    
    def getAliases(self):
        return self.aliases

    def getSeverity(self):
        return self.severity

    def getAffected(self):
        return self.affected

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
        try:
            url = "https://api.osv.dev/v1/query"
            obj = {
                "version": dependency.getVersion(),
                "package": {
                    "name": dependency.getName(),
                    "ecosystem": dependency.getEcosystem()
                }
            }


            if dependency.getVersion() == "-":
                obj = {
                "package": {
                    "name": dependency.getName(),
                    "ecosystem": dependency.getEcosystem()
                }
            }

            result = requests.post(url, json=obj)
            vulnDependency = result.json()

            return vulnDependency
        except Exception as e:
            logger.error(f"Error : {repr(e)}")

    # scan all vulnerability
    def scanDependencies(self):
        try:
            logger.info(f"Total dependencies: {len(self.getDependencies())}")
            logger.info("Scanning dependency vulnerabilities...")
            for dependency in self.getDependencies():
                result = self.scanDependency(dependency)
                if result:
                    # print(result.__dict__)
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
                            parsedRes["affected"]
                        )

                        self.addVulnerableDependency(vulnDep)
            logger.info("Completed scanning dependency vulnerabilities")
            logger.info(f"Vulnerabilities found: {len(self.getVulnerableDependencies())}")
        except Exception as e:
            logger.error(f"Error : {repr(e)}")

    # get important key from OSV response
    def parseDependencyResult(self, result):
        vulnResult = {}
        vulnResult["details"] = result.get("details")
        vulnResult["aliases"] = result.get("aliases")
        vulnResult["severity"] = result.get("severity")
        vulnResult["affected"] = result.get("affected")[0].get("ranges")
    
        return vulnResult

    def dumpVulnerabilities(self, filename):
        vulnerableDependenciesList = [x.getDependency() for x in self.getVulnerableDependencies()]
        if not os.path.exists("reports"):
            os.makedirs("reports")

        with open(f"reports/{str(date.today())}-{filename}-dependency.json", "w") as fileRes:
            fileRes.write(json.dumps(vulnerableDependenciesList, indent=4))


    # get all dependencies used in a code
    # legacy, not used
    def scanDependenciesUsingRegex(self, filePath):
        fileExtension = filePath.split(".")[-1]
        if fileExtension != "py":
            return

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
                            # print(f"{dependencyName} dependency found at line {lineNumber}")
                            importList.append(dependencyName)
            
            # remove duplicate item
            newImportList = list(set(importList))
            for item in newImportList:
                dep = Dependency(item, "-", "PyPI", filePath)
                self.addDependency(dep)

        except Exception as e:
            logger.error(f"Error : {repr(e)}")