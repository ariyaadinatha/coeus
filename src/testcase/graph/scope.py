class TestScope:
    def __init__(self) -> None:
        self.test = "class scope"

    def sampleFunction(self):
        test = "function scope inside class scope"
        print(test)

# scope: scope.py
globalScope = "global scope"

def sampleFunctionScope(self):
    variable = "function scope"
    # scope: scope.py\sampleFunctionScope
    globalScope = "uhuy"
    print(globalScope)

sampleFunctionScope(None)
print(globalScope)