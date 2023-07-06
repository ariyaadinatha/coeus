from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS, PYTHON_DATA_SCOPE_IDENTIFIERS
import uuid
from abc import ABC, abstractmethod

class IRConverter(ABC):
    def __init__(self, sources, sinks, sanitizers) -> None:
        self.sources = sources
        self.sinks = sinks
        self.sanitizers = sanitizers
        self.functionSymbolTable = {}
    
    def createCompleteTree(self, root: Node, filename: str) -> IRNode:
        irRoot = self.createAstTree(root, filename)
        self.registerFunctionsToSymbolTable(irRoot)
        self.addControlFlowEdgesToTree(irRoot)
        self.addDataFlowEdgesToTree(irRoot)

        return irRoot

    @abstractmethod
    def createAstTree(self, root: Node, filename: str) -> IRNode:
        pass

    @abstractmethod
    def addControlFlowEdgesToTree(self, root: IRNode):
        pass

    @abstractmethod
    def addDataFlowEdgesToTree(self, root: IRNode):
        pass

    def setNodeCallEdges(self, node: IRNode):
        if node.isIdentifierOfFunctionDefinition():
            # if use file directory as key
            # fileDirectory = node.filename
            # key = (node.content, fileDirectory)

            key = node.content

            # handle arrow function in js
            if node.parent.isAssignmentStatement() and node.parent.astChildren[1].isFunctionDefinition():
                parameters = node.parent.astChildren[1].getParameters()
            else:
                parameters = node.parent.getParameters()

            if parameters is None:
                parameters = []

            if key in self.functionSymbolTable:
                self.functionSymbolTable[key].append({
                    'filename': node.filename,
                    'arguments': [parameter.id for parameter in parameters],
                    'returns': []
                })
            else:
                self.functionSymbolTable[key] = [{
                    'filename': node.filename,
                    'arguments': [parameter.id for parameter in parameters],
                    'returns': []
                }]

        # handle return variable
        if node.isPartOfReturnStatement():
            key = node.getIdentifierFromFunctionDefinition()

            if key in self.functionSymbolTable:
                for func in self.functionSymbolTable[key]:
                    if func['filename'] == node.filename:
                        func['returns'].append(node.id)

    def registerFunctionsToSymbolTable(self, root: IRNode):
        # to keep track of all visited nodes
        visited = set()
        # for dfs
        stack: list[IRNode] = [root]

        while stack:
            node = stack.pop()
            visited.add(node.id)

            # do the ting
            self.setNodeCallEdges(node)
            stack.extend(reversed([child for child in node.astChildren]))

    @abstractmethod
    def createDataFlowTreeDFS(self, root: Node, filename: str) -> IRNode:
        pass

    @abstractmethod
    def setNodeDataFlowEdges(self, node: IRNode, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        pass

    @abstractmethod
    def determineScopeNode(self, node: IRNode, prevScope: str) -> str:
        pass
    
    @abstractmethod
    def connectDataFlowEdgeToOutsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, symbolTable):
        pass

    @abstractmethod
    def connectDataFlowEdgeToInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        pass

    # only for languages that don't have scopes in if else blocks
    # looking at you python
    @abstractmethod
    def connectDataFlowEdgeToInsideFromInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        pass
    
    @abstractmethod
    def isControlScope(self, scope: str) -> bool:
        pass

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ("\"", ".", ",", "=", "==", "(", ")", "[", "]", ":", ";", "?>", "$", "{", "}", "'", ".=", "comment")

        if node.type in ignoredList:
            return True
        
        return False
    
    def getControlId(self, scope: str) -> str:
        return scope[-32:] if self.isControlScope(scope) else ""
    
    def getLastScope(self, scope: str) -> str:
        return scope.rpartition("\\")[2]
    
    def getDataScope(self, scope: str) -> str:
        dataScope = scope
        while self.isControlScope(dataScope):
            dataScope, _, _ = dataScope.rpartition("\\")
            
        return dataScope
    
    def isInSameBlockScope(self, refScope: str, scope: str) -> bool:
        dataScope = scope

        while dataScope.find("\\") != -1:
            if dataScope == refScope:
                return True
            dataScope, _, _ = dataScope.rpartition("\\")

        return False
