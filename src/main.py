from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler
from codehandler import FileHandler
from codehandler import Code
from log import logger
import time

def dependencyVulnExample():
    dep = Dependency("jinja2", "2.4.1", "PyPI", "testcase/dependency")
    dh = DependencyHandler()
    dh.addDependency(dep)
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())

def getDependency():
    fh = FileHandler()
    dh = DependencyHandler()
    fh.getAllFilesFromRepository("/home/caffeine/Documents/Code/tugas-akhir/coeus")
    fh.getDependencies(dh)
    dh.scanDependencies()
    dh.dumpVulnerabilities()

def parseLanguage():
    fh = FileHandler()
    fh.getAllFilesFromRepository("/home/caffeine/Documents/Code/tugas-akhir/coeus/src/testcase/python")
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)
        parsed = code.parseLanguage()

        print(f"{codePath} : {parsed} \n")

if __name__ == "__main__":
    parseLanguage()
    # logger.info("=============== Starting coeus ===============")
    # startTime = time.time()
    # getDependency()
    # logger.info(f"Execution time: {(time.time() - startTime)}")
    # logger.info("=============== Successfully running coeus ===============")