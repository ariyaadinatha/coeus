from utils.intermediate_representation.exporter import IRNode
from utils.constant.intermediate_representation import JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS

class IRPython(IRNode):
    def __init__(self):
        pass
    
    def isIdentifier(self) -> bool:
        return self.type == "identifier"

    def isPartOfAssignment(self) -> bool:
        return (self.parent.type == "assignment_expression" or self.parent.type == "variable_declarator")
        
    def isCallExpression(self) -> bool:
        return self.parent.parent.type == "call_expression"

    def isControlIdentifier(self) -> bool:
        return self.type in JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS
    
    def hasControlScope(self) -> bool:
        return len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS