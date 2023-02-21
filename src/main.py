from dependencyhandler import DependencyHandler
from dependencyhandler import Dependency
from secrethandler import SecretDetection
from vulnhandler import VulnerableHandler
from codehandler import FileHandler
from codehandler import Code
from log import logger
import time

def dependencyVulnExample():
    dep = Dependency("urllib3", "1.26.4", "PyPI", "testcase/dependency")
    dh = DependencyHandler()
    dh.addDependency(dep)
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())
        print("")

def getDependency():
    fh = FileHandler()
    dh = DependencyHandler()
    fh.getAllFilesFromRepository("/home/caffeine/Documents/Code/tugas-akhir/bruh")
    fh.getDependencies(dh)
    dh.scanDependencies()
    dh.dumpVulnerabilities()

def parseLanguage():
    fh = FileHandler()
    fh.getAllFilesFromRepository("/home/caffeine/Documents/Code/tugas-akhir/coeus/src/testcase/python")
    result = []
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)

        # parsed = code.parseLanguage()
        # print(f"{codePath} : {parsed} \n")
        # code.traverseTree(code.getRootNode())
        # code.traverse_tree(code.getRootNode())
        # code.searchTree(code.getRootNode(), "assignment", result)
        code.getNodes(code.getRootNode(), "assignment", result)
        # code.getNodes(code.getRootNode(), "call", result)
    
    # print(result)

    # a=[list(d.keys())[0] for d in data]
    for item in result:
        print(list(item.keys()))

def secretDetection():
    fh = FileHandler()
    fh.getAllFilesFromRepository("/home/caffeine/Documents/Code/tugas-akhir/coeus/src/testcase/python")
    sc = SecretDetection()
    vh = VulnerableHandler()
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)
        code.searchTree(code.getRootNode(), "assignment", sc.getAssignmentList())

        # Secret Detection
        sc.wordlistDetection(code.getSourceCode(), vh, codePath)
        for i in (vh.getVulnerable()):
            print(i.getVulnerable())



if __name__ == "__main__":
    # dependencyVulnExample()
    # getDependency()
    # parseLanguage()
    secretDetection()
    # logger.info("=============== Starting coeus ===============")
    # startTime = time.time()
    # getDependency()
    # logger.info(f"Execution time: {(time.time() - startTime)}")
    # logger.info("=============== Successfully running coeus ===============")