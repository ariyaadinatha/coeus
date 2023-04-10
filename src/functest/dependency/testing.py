import unittest

from handler.dependency.dependencyhandler import Dependency, DependencyHandler, VulnerableDependency

class TestDependency(unittest.TestCase):
    def setUp(self):
        self.dependency1 = Dependency("ajv", "6.10.0", 
        "npm", "/home/caffeine/Documents/Code/vulnerable-app/NodeGoat/package-lock.json") # JavaScript

        self.dependency2 = Dependency("com.thoughtworks.xstream:xstream", "1.4.5", 
        "Maven", "/home/caffeine/Documents/Code/vulnerable-app/pom.xml") # Java

        self.dependency3 = Dependency("laravel/framework", "v7.17.2", 
        "Packagist", "testcase/basic/composer.lock") # PHP

        self.dependency4 = Dependency("sqlparse", "0.3.1", 
        "PyPI", "/home/caffeine/Documents/Code/vulnerable-app/pygoat/requirements.txt") # Python

    def test_dependency_name(self):
        self.assertEqual(self.dependency1.getName(), "ajv")
        self.assertEqual(self.dependency2.getName(), "com.thoughtworks.xstream:xstream")
        self.assertEqual(self.dependency3.getName(), "laravel/framework")
        self.assertEqual(self.dependency4.getName(), "sqlparse")
        
    def test_dependency_version(self):
        self.assertEqual(self.dependency1.getVersion(), "6.10.0")
        self.assertEqual(self.dependency2.getVersion(), "1.4.5")
        self.assertEqual(self.dependency3.getVersion(), "v7.17.2")
        self.assertEqual(self.dependency4.getVersion(), "0.3.1")

    def test_dependency_ecosystem(self):
        self.assertEqual(self.dependency1.getEcosystem(), "npm")
        self.assertEqual(self.dependency2.getEcosystem(), "Maven")
        self.assertEqual(self.dependency3.getEcosystem(), "Packagist")
        self.assertEqual(self.dependency4.getEcosystem(), "PyPI")
        
    def test_dependency_location(self):
        self.assertEqual(self.dependency1.getFileLocation(), "/home/caffeine/Documents/Code/vulnerable-app/NodeGoat/package-lock.json")
        self.assertEqual(self.dependency2.getFileLocation(), "/home/caffeine/Documents/Code/vulnerable-app/pom.xml")
        self.assertEqual(self.dependency3.getFileLocation(), "testcase/basic/composer.lock")
        self.assertEqual(self.dependency4.getFileLocation(), "/home/caffeine/Documents/Code/vulnerable-app/pygoat/requirements.txt")

class TestVulnerableDependency(unittest.TestCase):
    def setUp(self):
        self.vulnerableDependency = VulnerableDependency(
            "com.thoughtworks.xstream:xstream",
            "1.4.5",
            "Maven",
            "/home/caffeine/Documents/Code/vulnerable-app/pom.xml",
            "### Impact\nThe vulnerability may allow a remote attacker to load and execute arbitrary code from a remote host only by manipulating the processed input stream, if using the version out of the box with Java runtime version 14 to 8 or with JavaFX installed. No user is affected, who followed the recommendation to setup XStream's security framework with a whitelist limited to the minimal required types.\n\n### Patches\nXStream 1.4.18 uses no longer a blacklist by default, since it cannot be secured for general purpose.\n\n### Workarounds\nSee [workarounds](https://x-stream.github.io/security.html#workaround) for the different versions covering all CVEs.\n\n### References\nSee full information about the nature of the vulnerability and the steps to reproduce it in XStream's documentation for [CVE-2021-39153](https://x-stream.github.io/CVE-2021-39153.html).\n\n### Credits\nCeclin and YXXX from the Tencent Security Response Center found and reported the issue to XStream and provided the required information to reproduce it.\n\n### For more information\nIf you have any questions or comments about this advisory:\n* Open an issue in [XStream](https://github.com/x-stream/xstream/issues)\n* Contact us at [XStream Google Group](https://groups.google.com/group/xstream-user)\n",
            ["CVE-2021-39153"],
            [{
                "type": "CVSS_V3",
                "score": "CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:C/C:H/I:H/A:H"
            }],
            [{
                "type": "ECOSYSTEM",
                "events": [
                    {"introduced": "0"},
                    {"fixed": "1.4.18"}
                ]
            }]
        )

    def test_get_details(self):
        self.assertEqual(self.vulnerableDependency.getDetails(),
            "### Impact\nThe vulnerability may allow a remote attacker to load and execute arbitrary code from a remote host only by manipulating the processed input stream, if using the version out of the box with Java runtime version 14 to 8 or with JavaFX installed. No user is affected, who followed the recommendation to setup XStream's security framework with a whitelist limited to the minimal required types.\n\n### Patches\nXStream 1.4.18 uses no longer a blacklist by default, since it cannot be secured for general purpose.\n\n### Workarounds\nSee [workarounds](https://x-stream.github.io/security.html#workaround) for the different versions covering all CVEs.\n\n### References\nSee full information about the nature of the vulnerability and the steps to reproduce it in XStream's documentation for [CVE-2021-39153](https://x-stream.github.io/CVE-2021-39153.html).\n\n### Credits\nCeclin and YXXX from the Tencent Security Response Center found and reported the issue to XStream and provided the required information to reproduce it.\n\n### For more information\nIf you have any questions or comments about this advisory:\n* Open an issue in [XStream](https://github.com/x-stream/xstream/issues)\n* Contact us at [XStream Google Group](https://groups.google.com/group/xstream-user)\n"
        )

    def test_get_aliases(self):
        self.assertEqual(self.vulnerableDependency.getAliases(), ["CVE-2021-39153"])

    def test_get_severity(self):
        self.assertEqual(self.vulnerableDependency.getSeverity(), [{
            "type": "CVSS_V3",
            "score": "CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:C/C:H/I:H/A:H"
        }])

    def test_get_affected(self):
        self.assertEqual(self.vulnerableDependency.getAffected(), [{
            "type": "ECOSYSTEM",
            "events": [
                {"introduced": "0"},
                {"fixed": "1.4.18"}
            ]
        }])

class TestDependencyHandler(unittest.TestCase):
    def setUp(self):
        self.dependency1 = Dependency("ajv", "6.10.0", 
        "npm", "/home/caffeine/Documents/Code/vulnerable-app/NodeGoat/package-lock.json") # JavaScript

        self.dependency2 = Dependency("com.thoughtworks.xstream:xstream", "1.4.5", 
        "Maven", "/home/caffeine/Documents/Code/vulnerable-app/pom.xml") # Java

        self.dependency3 = Dependency("laravel/framework", "v7.17.2", 
        "Packagist", "testcase/basic/composer.lock") # PHP

        self.dependency4 = Dependency("sqlparse", "0.3.1", 
        "PyPI", "/home/caffeine/Documents/Code/vulnerable-app/pygoat/requirements.txt") # Python

        self.vulnerableDependency1 = VulnerableDependency(
            "ajv",
            "6.10.0",
            "npm",
            "/home/caffeine/Documents/Code/vulnerable-app/NodeGoat/package-lock.json",
            "An issue was discovered in ajv.validate() in Ajv (aka Another JSON Schema Validator) 6.12.2. A carefully crafted JSON schema could be provided that allows execution of other code by prototype pollution. (While untrusted schemas are recommended against, the worst case of an untrusted schema should be a denial of service, not execution of code.)",
            ["CVE-2020-15366"],
            [{
                "type": "CVSS_V3",
                "score": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:L"
            }],
            [{
                "type": "SEMVER",
                "events": [
                    {"introduced": "0"},
                    {"fixed": "6.12.3"}
                ]
            }]
        )

        self.vulnerableDependency2 = VulnerableDependency(
            "sqlparse",
            "0.3.1",
            "PyPI",
            "/home/caffeine/Documents/Code/vulnerable-app/pygoat/requirements.txt",
            "sqlparse is a non-validating SQL parser module for Python. In sqlparse versions 0.4.0 and 0.4.1 there is a regular Expression Denial of Service in sqlparse vulnerability. The regular expression may cause exponential backtracking on strings containing many repetitions of '\r\n' in SQL comments. Only the formatting feature that removes comments from SQL statements is affected by this regular expression. As a workaround don't use the sqlformat.format function with keyword strip_comments=True or the --strip-comments command line flag when using the sqlformat command line tool. The issues has been fixed in sqlparse 0.4.2.",
            ["CVE-2021-32839", "GHSA-p5w8-wqhj-9hhf"],
            None,
            [{
                "type": "GIT", 
                "repo": "https://github.com/andialbrecht/sqlparse", 
                "events": [
                    {"introduced": "0"}, 
                    {"fixed": "8238a9e450ed1524e40cb3a8b0b3c00606903aeb"}
                ]},
            {
                "type": "ECOSYSTEM", 
                "events": [
                    {"introduced": "0"}, 
                    {"fixed": "0.4.2"}
                ]}
            ])

        self.dependencyHandler = DependencyHandler()

    def test_dependency_handler_get(self):
        self.assertEqual(len(self.dependencyHandler.getDependencies()), 0)
        self.assertEqual(len(self.dependencyHandler.getVulnerableDependencies()), 0)

    def test_dependency_handler_add(self):
        self.dependencyHandler.addDependency(self.dependency1)
        self.assertEqual(len(self.dependencyHandler.getDependencies()), 1)
        self.assertEqual(self.dependencyHandler.getDependencies()[0], self.dependency1)

    def test_dependency_handler_add_vulnerable(self):
        self.dependencyHandler.addVulnerableDependency(self.vulnerableDependency1)
        self.assertEqual(len(self.dependencyHandler.getVulnerableDependencies()), 1)
        self.assertEqual(self.dependencyHandler.getVulnerableDependencies()[0], self.vulnerableDependency1)
        
    def test_dependency_handler_multiple_add(self):
        self.dependencyHandler.addDependency(self.dependency1)
        self.dependencyHandler.addDependency(self.dependency2)
        self.assertEqual(len(self.dependencyHandler.getDependencies()), 2)
        self.assertEqual(self.dependencyHandler.getDependencies()[0], self.dependency1)
        self.assertEqual(self.dependencyHandler.getDependencies()[1], self.dependency2)

    def test_dependency_handler_scan_dependency(self):
        pass
        # self.assertEqual(self.dependencyHandler.scanDependency(self.dependency1)["vulns"], self.vulnerableDependency1)
        # self.assertEqual(len(self.dependencyHandler.getVulnerableDependencies()), 1)
        # self.assertEqual(self.dependencyHandler.getVulnerableDependencies(), self.vulnerableDependency1)

    def test_dependency_handler_multiple_scan_dependency(self):
        pass
        self.dependencyHandler.addDependency(self.dependency4)
        # self.dependencyHandler.addDependency(self.dependency4)
        self.dependencyHandler.scanDependencies()
        self.assertEqual(len(self.dependencyHandler.getVulnerableDependencies()), 1)
        self.assertEqual(self.dependencyHandler.getVulnerableDependencies()[0], self.vulnerableDependency2)

if __name__ == '__main__':
    unittest.main()