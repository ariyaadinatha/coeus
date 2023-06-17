from tree_sitter import Node
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS, JAVASCRIPT_CONTROL_STATEMENTS, JAVASCRIPT_DIVERGE_CONTROL_STATEMENTS
from typing import Union
import uuid

# all node from tree-sitter parse result
class IRJavascriptNode(IRNode):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        super().__init__(node, filename, projectId, controlId, parent)

    def isCallExpression(self) -> bool:
        return self.type == "call_expression"
        
    def isInsideIfElseBranch(self) -> bool:
        return self.scope != None and len(self.scope.rpartition("\\")[2]) > 32 and self.scope.rpartition("\\")[2][:-32] in JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS
    
    def isPartOfAssignment(self) -> bool:
        if self.parent is not None:
            if self.parent.type == "assignment_expression" or self.parent.type == "variable_declarator":
                return True
        return False
    
    def isControlStatement(self) -> bool:
        return self.type in JAVASCRIPT_CONTROL_STATEMENTS
    
    def isDivergingControlStatement(self) -> bool:
        return self.type in JAVASCRIPT_DIVERGE_CONTROL_STATEMENTS
    
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
        return self.type == "if_statement" and self.parent.type == "else_clause"
    
    def isElseInElseIfBranch(self) -> bool:
        return self.type == "else_clause" and self.parent.type == "if_statement" and self.parent.parent.type == "else_clause"
    
    def isInElseIfBranch(self) -> bool:
        return self.parent is not None and self.parent.type == "statement_block" and (self.parent.parent.isElseIfBranch() or self.parent.parent.isElseInElseIfBranch())

    def getRootIfStatement(self) -> IRNode:
        # skip block node
        ifStatementChain = self.parent

        while ifStatementChain.parent.type == "if_statement" or ifStatementChain.parent.type == "else_clause":
            ifStatementChain = ifStatementChain.parent

        return ifStatementChain
    
    def isFirstStatementInBlock(self) -> IRNode:
        return self.node.prev_sibling.type == "{"