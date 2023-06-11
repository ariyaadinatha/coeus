import json
import re

exclussion = [
    "\n", 
    "\\s",
    "\\$(\\w+)",
    "\\$(.*)",
    "(.*)\/WebGoat\/(.*)",
    "(.*)string(.*)",
    "(.*)this(.*)",
    "(.*)char(.*)",
    "(.*)array(.*)",
    "(.*)get(.*)",
    "(.*)toString(.*)",
    "(.*)Date(.*)",
    "(.*)Lesson(.*)",
    "(.*)ange(.*)",
    "(.*)unction(.*)",
    "(.*)ays(.*)",
    "(.*)access(.*)",
    "(.*)refresh(.*)",
    "(.*)ist(.*)",
    "(.*)ore(.*)",
    "(.*)atcher(.*)"
]

def scanSecretVariable(variableValue):
    excludedPattern = [re.compile(x) for x in exclussion]
    # find variable in excluded pattern
    for pattern in excludedPattern:
        if pattern.search(variableValue):
            return 1
    
    return 0

with open("webgoat.json", 'r') as file:
    webgoat = json.load(file)
###################### PHP ###################################
passKey = ["url", "containsString", "MockMvcRequestBuilders", "node", "Date", "keyCode", "toolbar.find", "Lists",
"range.getNodes", "range.setStart", "bindKey", "parseInt", "RegExp", "Modernizr.addTest", "connection", "startLesson", "checkAssignment", 
"classes", "decode", "encode", "isNaN", "refreshToken", "resource", "resources", "useragent", "params", "session",
"userSessionData", "submittedAnswers", "submittedQuestions"
]
passVal = ["decode", "encode", "JWTToken", "hiddenMenu1", "hiddenMenu2", "compact", 
"access_token", "refresh_token", "objectMapper", "readValue", "Map", "tokens", "websession", "resourceLoader", "asString", "cookie"]

passSymbol = ["(", "$", ")", "/", "_", ")"]
passPrefix = ["array", "document", "formdata", "registry", "secQuestionStore", "WireMock", "session"]

lowercaseVal = [item.lower() for item in passVal]
lowercaseKey = [item.lower() for item in passKey]

total = 0 
vale = []
for result in webgoat:
    vale.append(result["evidence"])

####################################### PYTHON ########################################

exclussion = [
    "\n", 
    "\\s",
]

passKey = ["render", "test_bench", "urlpatterns", "fetch"]
passVal = []
passSymbol = []
passPrefix = ["subprocess", "response", "models", "datetime", "request", "migrations"]

####################################### PHP ########################################


bruh = sorted(webgoat, key=lambda x: list(x["evidence"].keys())[0].lower())
# bruh = sorted(vale, key=lambda x: list(x.keys())[0].lower())

# print(bruh)

newDict = []

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

    elif len(key.split(".")[0]) < 5:
        pass

    elif len(key.split(".")[0]) < 5:
        pass

    elif key.split(".")[0].lower() in passPrefix:
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
with open(f"filtered-webgoat.json", "w") as fileRes:
    fileRes.write(json.dumps(newDict, indent=4))

