from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS, PYTHON_CONTROL_STATEMENTS, PYTHON_DIVERGE_CONTROL_STATEMENTS
from typing import Union
import uuid

# all node from tree-sitter parse result
class IRPythonNode(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        super().__init__(node, filename, projectId, controlId, parent)

    def isCallExpression(self) -> bool:
        return self.type == "call"
        
    def isInsideIfElseBranch(self) -> bool:
        return self.scope != None and len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in PYTHON_CONTROL_SCOPE_IDENTIFIERS
    
    def isControlStatement(self) -> bool:
        return self.type in PYTHON_CONTROL_STATEMENTS
    
    def isDivergingControlStatement(self) -> bool:
        return self.type in PYTHON_DIVERGE_CONTROL_STATEMENTS
    
    def isIdentifierOfFunctionDefinition(self) -> bool:
        return self.isIdentifier() and self.parent.isFunctionDefinition()
    
    def isArgumentOfAFunctionDefinition(self) -> str:
        return self.isIdentifier() and self.parent.type == "parameters"
    
    def isArgumentOfAFunctionCall(self) -> str:
        return self.isIdentifier() and self.parent.type == "argument_list"
    
    def getParameters(self) -> list:
        for child in self.astChildren:
            if child.type == "parameters":
                return child.astChildren
    
    def isBinaryExpression(self) -> bool:
        return self.type == "binary_operator"
    
    def getIdentifierFromAssignment(self) -> str:
        # a = x
        # a = "test" + x
        parent = self.parent
        while parent.type != "assignment":
            parent = parent.parent

            if parent is None:
                return None
        if self.node.prev_sibling is not None and self.node.prev_sibling.prev_sibling is not None and self.node.prev_sibling.type == "=" and self.node.prev_sibling.prev_sibling.type == "identifier":
            return self.node.prev_sibling.prev_sibling.text.decode("UTF-8")
        else:
            # a = "test" + x
            return parent.astChildren[0].content