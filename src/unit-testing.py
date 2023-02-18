import unittest
from dependencyhandler import Dependency
from dependencyhandler import DependencyHandler

class TestDependency(unittest.TestCase):
    def test_dependency(self):
        dependency = Dependency("DepName", "1.0", "/path/code.py")
        self.assertEqual(dependency.getName(), "DepName")
        self.assertEqual(dependency.getVersion(), "1.0")
        self.assertEqual(dependency.getFileLocation(), "/path/code.py")
    
    def test_dependencyhandler(self):
        test = Dependency("Hello", "1.0", "path/code.py")
        test2 = Dependency("Hello2", "2.0", "path/code.py")

        all = DependencyHandler()
        all.addDependencies(test)
        all.addDependencies(test2)

        self.assertEqual(len(all.getDependencies()), 2)
        self.assertEqual(all.getDependencies()[0], test)
        self.assertEqual(all.getDependencies()[1], test2)

if __name__ == '__main__':
    unittest.main()
