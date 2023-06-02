from utils.intermediate_representation.converter.converter import IRNode
from tree_sitter import Node
from utils.constant.intermediate_representation import JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS

class IRJavascript(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, language: str, controlId=None, parent=None) -> None:
        IRNode.__init__(self, node, filename, projectId, language, controlId, parent)
    
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