from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import PHP_CONTROL_SCOPE_IDENTIFIERS
from typing import Union
import uuid

# all node from tree-sitter parse result
class IRPhpNode(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        super().__init__(node, filename, projectId, controlId, parent)

    def isCallExpression(self) -> bool:
        return self.type == "member_call_expression" or self.type == "type_call_expression"
        
    def isInsideIfElseBranch(self) -> bool:
        return self.scope != None and len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in PHP_CONTROL_SCOPE_IDENTIFIERS
    
    def isPartOfAssignment(self) -> bool:
        return self.parent is not None and self.parent.type == "assignment_expression"