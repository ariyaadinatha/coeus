from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import PHP_CONTROL_SCOPE_IDENTIFIERS, PHP_CONTROL_STATEMENTS, PHP_DIVERGE_CONTROL_STATEMENTS
from typing import Union
import uuid

# all node from tree-sitter parse result
class IRPhpNode(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        super().__init__(node, filename, projectId, controlId, parent)

    def isCallExpression(self) -> bool:
        return "call_expression" in self.type or "echo" in self.type
        
    def isInsideIfElseBranch(self) -> bool:
        return self.scope != None and len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in PHP_CONTROL_SCOPE_IDENTIFIERS
        
    def isControlStatement(self) -> bool:
        return self.type in PHP_CONTROL_STATEMENTS
    
    def isDivergingControlStatement(self) -> bool:
        return self.type in PHP_DIVERGE_CONTROL_STATEMENTS
    
    # TODO: implement this func to add parameters to symbol table
    def isArgumentOfAFunctionDefinition(self) -> str:
        return super().isArgumentOfAFunctionDefinition()
    
    def isBinaryExpression(self) -> bool:
        return self.type == "binary_expression"
    
    def getIdentifierFromAssignment(self) -> str:
        parent = self.parent
        while "assignment_expression" not in parent.type:
            parent = parent.parent

            if parent is None:
                return None
        if self.node.prev_sibling is not None and self.node.prev_sibling.prev_sibling is not None and self.node.prev_sibling.type == "=" and self.node.prev_sibling.prev_sibling.type == "variable_name":
            return self.node.prev_sibling.prev_sibling.text.decode("UTF-8")
        else:
            # a = "test" + x
            return parent.astChildren[0].content