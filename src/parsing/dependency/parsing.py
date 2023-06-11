import json

# dari npm
with open("node", "r") as file:
    # Read the contents of the file
    content = file.readlines()
content = [line.strip() for line in content]
removeDuplicate = list(set(content))

# OSV
with open("nodegoat.txt", "r") as file:
    # Read the contents of the file
    node = file.readlines()
node = [line.strip() for line in node]

# log
with open("coeus.log", "r") as file:
    # Read the contents of the file
    log = file.readlines()
log = [line.strip() for line in log]

# static analysis
with open("node.json", 'r') as file:
    goat = json.load(file)

def countOSV():
    count_dict = {}
    for item in node:
        if item in count_dict:
            count_dict[item] += 1
        else:
            count_dict[item] = 1

    for i in count_dict:
        print(f"{count_dict[i]}:{i}")

def countLog():
    remDup = list(set(node))
    # print("count log")
    for item in remDup:
        if item not in log:
            print(item)


def countTrue():
    newList = []
    for i in goat:
        a = f"{i['name']}@{i['version']}"
        newList.append(a)
    removeDup = list(set(newList))
    removeOSV = list(set(node))

    for i in removeOSV:
        if i not in removeDup:
            print(i)


newList = []
newDict = {}

def countAnalysis():
    # Count the items
    for item in newList:
        if item in newDict:
            newDict[item] += 1
        else:
            newDict[item] = 1

    # Print the dictionary
    for i in newDict:
        print(f"{newDict[i]}:{i}")

# countAnalysis()
countTrue()




