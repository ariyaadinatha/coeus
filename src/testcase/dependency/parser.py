import re

regexPattern = {
                "requirements": [ # python extension
                    re.compile('(?<=^import ).*'), # get words starting with import
                    re.compile('(?<=^from ).*?(?= import)') # get words between from and import
                ]
        }
importList = []

with open('requirements.txt', 'r') as file:
    for lineNumber, line in enumerate(file, start=1):
        for pattern in regexPattern["requirements"]:
            result = (pattern.search(line))
            if result:
                dependencyName = result.group(0)
                print(f"{dependencyName} dependency found at line {lineNumber}")
                importList.append(dependencyName)
        print(line)
        break
    #data = file.read()

# print(data)