class Vulnerable:
    def __init__(self, title, details, aliases, severity, evidence, files, line, date):
        self.title = title
        self.details = details
        self.aliases = aliases
        self.severity = severity
        self.evidence = evidence
        self.files = files
        self.line = line
        self.date = date

    def getTitle(self):
        return self.title
    
    def getDetails(self):
        return self.details
    
    def getAliases(self):
        return self.aliases
    
    def getSeverity(self):
        return self.severity
    
    def getEvidence(self):
        return self.evidence
    
    def getFiles(self):
        return self.files

    def getLine(self):
        return self.line
    
    def getDate(self):
        return self.date

    def getVulnerable(self):
        return self.__dict__

class VulnerableHandler:
    def __init__(self):
        self.vulnerableList = []

    def getVulnerable(self):
        return self.vulnerableList

    def addVulnerable(self, vuln):
        self.vulnerableList.append(vuln)

