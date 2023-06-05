from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS
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
        return self.type in PYTHON_CONTROL_SCOPE_IDENTIFIERS
    
    def getIdentifierFromAssignment(self) -> str:
        # a = x
        # a = "test" + x
        parent = self.parent
        while parent.type != "assignment":
            parent = parent.parent
        if self.node.prev_sibling.prev_sibling is not None and self.node.prev_sibling.type == "=" and self.node.prev_sibling.prev_sibling.type == "identifier":
            return self.node.prev_sibling.prev_sibling.text.decode("UTF-8")
        else:
            # a = "test" + x
            return parent.astChildren[0].content
    
    def isPartOfAssignment(self) -> bool:
        if "statement" in self.type:
            return False
        
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.type == "assignment":
                return True
            parent = parent.parent

        return False
    
    def isPartOfCallExpression(self) -> bool:
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isCallExpression():
                return True
            parent = parent.parent

        return False
    
    def getCallExpression(self) -> IRNode:
        parent = self.parent

        while not parent.isCallExpression():
            parent = parent.parent

        return parent
