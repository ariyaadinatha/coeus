from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler
from codehandler import CodeHandler
from log import logger
import time

def dependencyVulnExample():
    dep = Dependency("jinja2", "2.4.1", "PyPI", "testcase/dependency")
    dh = DependencyHandler()
    dh.addDependency(dep)
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())

def getDependenccy():
    ch = CodeHandler()
    dh = DependencyHandler()
    ch.getAllFilesFromRepository("/home/adinatha/Documents/Programming/tugas-akhir/coeus")
    # print(ch.getDependencyFilesPath())
    ch.getDependencies(dh)
    # for item in dh.getDependencies():
    #     print(item.getDependency())
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())
    #### !!!!! TO DO, FIX DUMP FEATURE !!!!! ####
    # dh.dumpVulnerabilities()
    

if __name__ == "__main__":
    logger.info("=============== Starting coeus ===============")
    startTime = time.time()
    getDependenccy()
    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Successfully running coeus ===============")