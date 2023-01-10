from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler
from codehandler import CodeHandler

if __name__ == "__main__":
    # ch = CodeHandler()
    # ch.getAllFilesFromRepository("testcase")
    # d = DependencyHandler()
    # for filePath in ch.getImportantFiles():
    #     d.scanDependenciesUsingRegex(filePath)

    dep = Dependency("jinja2", "2.4.1", "PyPI", "testcase/dependency")
    dh = DependencyHandler()
    dh.addDependency(dep)
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())