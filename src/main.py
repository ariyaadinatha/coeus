from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.dependency.secrethandler import SecretDetection
from utils.vulnhandler import VulnerableHandler
from utils.codehandler import FileHandler
from utils.codehandler import Code
from utils.log import logger
from utils.intermediate_representation.converter import IRConverter
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
    fh.getAllFilesFromRepository("./testcase/python")
    result = []
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)

        parsed = code.parseLanguage()
        print(f"{codePath} : {parsed} \n")

        # code.traverseTree(code.getRootNode())
        # code.traverse_tree(code.getRootNode())
        # code.searchTree(code.getRootNode(), "assignment", result)
        # code.getNodes(code.getRootNode(), "assignment", result)
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
        code = Code("javascript", sourceCode)
        code.searchTree(code.getRootNode(), "assignment", sc.getAssignmentList())
        code.searchTree(code.getRootNode(), "argument_list", sc.getAssignmentList())

        # Secret Detection
        sc.valueDetection(code.getSourceCode(), vh, codePath)
        sc.clearAssignmentList()
        # for i in (vh.getVulnerable()):
        #     print(i.getVulnerable())

def injection():
    fh = FileHandler()
    fh.getAllFilesFromRepository("./testcase/python")
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)

        print(codePath)

        root = code.getRootNode()
        parsed = code.parseLanguage()
        tree = code.getTree()

        # ***: export tree to CSV
        # code.traverseTree(root, [])
        # code.createTreeListWithId(root, code.treeList, "parent")
        # code.exportToCSV()

        # ***: convert node to IR
        converter = IRConverter()
        astRoot = converter.createAstTree(root)
        converter.printTree(astRoot)

if __name__ == "__main__":
    # dependencyVulnExample()
    # getDependency()
    # parseLanguage()
    # secretDetection()
    
    injection()
    
    
    
    
    
    
    
    
    
    # logger.info("=============== Starting coeus ===============")
    # startTime = time.time()
    # getDependency()
    # logger.info(f"Execution time: {(time.time() - startTime)}")
    # logger.info("=============== Successfully running coeus ===============")

    
