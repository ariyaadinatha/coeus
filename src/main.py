from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler
from codehandler import CodeHandler

if __name__ == "__main__":
    ch = CodeHandler()
    ch.getAllFilesFromRepository("testcase")
    d = DependencyHandler()
    for filePath in ch.getImportantFiles():
        d.scanDependencies(filePath)