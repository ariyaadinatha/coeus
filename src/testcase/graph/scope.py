class TestScope:
    def __init__(self) -> None:
        self.test = "class scope"

    def sampleFunction(self):
        test = "function scope inside class scope"
        print(test)

globalScope = "global scope"

def sampleFunctionScope(self):
    variable = "function scope"
    globalScope = "uhuy"
    print(globalScope)

sampleFunctionScope(None)
print(globalScope)