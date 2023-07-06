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
    
    def isControlStatement(self) -> bool:
        return self.type in JAVASCRIPT_CONTROL_STATEMENTS
    
    def isDivergingControlStatement(self) -> bool:
        return self.type in JAVASCRIPT_DIVERGE_CONTROL_STATEMENTS
    
    def isIdentifierOfFunctionDefinition(self) -> bool:
        if not self.isIdentifier():
            return False
        if self.parent is None:
            return False

        # handle standard function definition and arrow function definition
        return self.parent.isFunctionDefinition() or (self.parent.isAssignmentStatement() and len(self.parent.astChildren) >= 2 and self.parent.astChildren[1].isFunctionDefinition())
    
    def isArgumentOfAFunctionDefinition(self) -> str:
        return self.isIdentifier() and self.parent.type == "formal_parameters"
    
    def isArgumentOfAFunctionCall(self) -> str:
        return self.isIdentifier() and self.parent.type == "arguments"
    
    def getParameters(self) -> list:
        for child in self.astChildren:
            if child.type == "formal_parameters":
                return child.astChildren
    
    def isBinaryExpression(self) -> bool:
        return self.type == "binary_expression"
    
    def getIdentifierFromAssignment(self) -> str:
        # a = x
        # a = "test" + x
        parent = self.parent
        while "assignment" not in parent.type and "declarator" not in parent.type:
            parent = parent.parent

            if parent is None:
                return None
        if self.node.prev_sibling is not None and self.node.prev_sibling.prev_sibling is not None and self.node.prev_sibling.type == "=" and self.node.prev_sibling.prev_sibling.type == "identifier":
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
    
    def isBlockScopeVariableInAssignment(self) -> IRNode:
        return self.isIdentifier() and self.parent.parent.type == "lexical_declaration"