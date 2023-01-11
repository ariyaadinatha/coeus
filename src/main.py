from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler
from codehandler import CodeHandler

def dependencyVulnExample():
    dep = Dependency("jinja2", "2.4.1", "PyPI", "testcase/dependency")
    dh = DependencyHandler()
    dh.addDependency(dep)
    dh.scanDependencies()
    for item in dh.getVulnerableDependencies():
        print(item.getDependency())

if __name__ == "__main__":
    dependencyVulnExample()