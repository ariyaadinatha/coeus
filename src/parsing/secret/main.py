import json
import re

exclussion = [
]

def scanSecretVariable(variableValue):
    excludedPattern = [re.compile(x) for x in exclussion]
    # find variable in excluded pattern
    for pattern in excludedPattern:
        if pattern.search(variableValue):
            return 1
    
    return 0

with open("nodegoat.json", 'r') as file:
    webgoat = json.load(file)


passKey = ["RegExp"]
passVal = []
passSymbol = []
passPrefix = ["Math", "Raphael", "this", "Date"]

lowercaseVal = [item.lower() for item in passVal]
lowercaseKey = [item.lower() for item in passKey]

total = 0 
vale = []
newDict = []

for result in webgoat:
    vale.append(result["evidence"])

bruh = sorted(webgoat, key=lambda x: list(x["evidence"].keys())[0].lower())
# bruh = sorted(vale, key=lambda x: list(x.keys())[0].lower())

# print(bruh)
# for item in bruh:
#     print(item)


# if total == 1:
for item in bruh:
    val = item["evidence"]
    # Access and print the value
    key = next(iter(val))
    value = next(iter(val.values()))
    if key.lower() in lowercaseKey:
        pass

    elif len(key) < 3:
        pass

    elif len(key.split(".")[0]) < 3:
        pass

    elif key.split(".")[0].lower() in passPrefix:
        pass

    elif value.split(".")[0].lower() in passPrefix:
        pass

    elif key[0] in passSymbol:
        pass

    elif len(value) < 3:
        pass

    elif value.lower() in lowercaseVal:
        pass

    elif scanSecretVariable(value):
        pass

    else:
        total += 1
        newDict.append(item)
        print(key.replace("\n","").replace(" ",""), value.replace("\n",""))

print(total)
with open(f"aaa-nodegoat.json", "w") as fileRes:
    fileRes.write(json.dumps(newDict, indent=4))

