from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import JAVA_CONTROL_SCOPE_IDENTIFIERS, JAVA_CONTROL_STATEMENTS, JAVA_DIVERGE_CONTROL_STATEMENTS
from typing import Union
import uuid

# all node from tree-sitter parse result
class IRJavaNode(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        super().__init__(node, filename, projectId, controlId, parent)

    def isCallExpression(self) -> bool:
        return "invocation" in self.type
        
    def isInsideIfElseBranch(self) -> bool:
        return self.scope != None and len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in JAVA_CONTROL_SCOPE_IDENTIFIERS
    
    def isControlStatement(self) -> bool:
        return self.type in JAVA_CONTROL_STATEMENTS
    
    def isDivergingControlStatement(self) -> bool:
        return self.type in JAVA_DIVERGE_CONTROL_STATEMENTS
    
    def getIdentifierFromAssignment(self) -> str:
        # a = x
        # a = "test" + x
        parent = self.parent
        while parent.type != "assignment":
            parent = parent.parent

            if parent is None:
                return None
        if self.node.prev_sibling.prev_sibling is not None and self.node.prev_sibling.type == "=" and self.node.prev_sibling.prev_sibling.type == "identifier":
            return self.node.prev_sibling.prev_sibling.text.decode("UTF-8")
        else:
            # a = "test" + x
            return parent.astChildren[0].content
        
    def isElseIfBranch(self) -> bool:
        return self.type == "if_statement" and self.parent.type == "if_statement"
    
    def isInElseIfBranch(self) -> bool:
        return self.parent is not None and self.parent.type == "block" and self.parent.parent.isElseIfBranch()

    def getRootIfStatement(self) -> IRNode:
        # skip block node
        ifStatementChain = self.parent

        while ifStatementChain.parent.type == "if_statement":
            ifStatementChain = ifStatementChain.parent

        return ifStatementChain
    
    def isFirstStatementInBlock(self) -> IRNode:
        return self.node.prev_sibling.type == "{"