from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.intermediate_representation.nodes.irjavascriptnode import IRJavascriptNode
from utils.intermediate_representation.converter.converter import IRConverter
from utils.constant.intermediate_representation import JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS, JAVASCRIPT_DATA_SCOPE_IDENTIFIERS
import uuid
from abc import ABC, abstractmethod

class IRJavascriptConverter(IRConverter):
    def __init__(self, sources, sinks, sanitizers) -> None:
        IRConverter.__init__(self, sources, sinks, sanitizers)

    def createCompleteTreeDFS(self, root: Node, filename: str) -> IRNode:
        irRoot = self.createDataFlowTreeDFS(root, filename)
        self.addControlFlowEdgesToTree(irRoot)

        return irRoot
    
    def createCompleteTree(self, root: Node, filename: str) -> IRNode:
        irRoot = self.createAstTree(root, filename)
        self.addControlFlowEdgesToTree(irRoot)
        self.addDataFlowEdgesToTreeDFS(irRoot)

        return irRoot

    def createAstTree(self, root: Node, filename: str) -> IRNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        projectId = uuid.uuid4().hex
        irRoot = IRJavascriptNode(root, filename, projectId)

        queue: list[tuple(IRNode, Union[IRNode, None])] = [(root, None)]

        while len(queue) != 0:
            currentPayload = queue.pop(0)
            node: Node = currentPayload[0]
            parent: IRNode = currentPayload[1]

            if self.isIgnoredType(node):
                continue

            convertedNode = IRJavascriptNode(node, filename, projectId, parent=parent)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                irRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return irRoot

    def addControlFlowEdgesToTree(self, root: IRNode):
        queue: list[tuple(IRNode, int, IRNode)] = [(root, 0, None)]

        while len(queue) != 0:
            currPayload = queue.pop(0)
            currNode: IRJavascriptNode = currPayload[0]
            statementOrder: int = currPayload[1]
            cfgParentId: str = currPayload[2]


            if statementOrder != 0:
                currNode.addControlFlowEdge(statementOrder, cfgParentId)
            
            # handle if and else statement
            if (currNode.isControlStatement() or currNode.isDivergingControlStatement()) and (not currNode.isElseIfBranch() and not currNode.isElseInElseIfBranch()):
                for child in currNode.astChildren:
                    if child.type == "statement_block":
                        blockNode = child
                        if len(blockNode.astChildren) != 0:
                            # connect if true statements with control statement and skip block node
                            if currNode.isControlStatement():
                            # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.id, f"{currNode.type}_child")
                            elif currNode.isDivergingControlStatement():
                            # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.parentId, f"{currNode.type}_child")
                    # handle inline if statement
                    elif "statement" in child.type:
                        child.addControlFlowEdge(1, currNode.id, f"{currNode.type}_child")
            # handle else if and else in else if statement
            elif currNode.isInElseIfBranch() and currNode.isFirstStatementInBlock():
                if currNode.parent.node.prev_sibling.type == "else":
                    controlType = "else_clause_child"
                else:
                    controlType = "else_if_clause_child"
                rootIfStatement: IRJavascriptNode = currNode.getRootIfStatement()
                currNode.addControlFlowEdge(1, rootIfStatement.id, controlType)
            
            statementOrder = 0
            # handles the next statement relationship
            currCfgParent = None if currNode.type != "program" else currNode.id
            for child in currNode.astChildren:
                if ("statement" in child.type or "declaration" in child.type) and child.type != "statement_block":
                    statementOrder += 1
                    queue.append((child, statementOrder, currCfgParent))
                    currCfgParent = child.id
                else:
                    queue.append((child, 0, None))

    def addDataFlowEdgesToTreeDFS(self, root: IRNode):
        # to keep track of all visited nodes
        visited = set()
        # to keep track of order of visited nodes
        visitedList = []
        # to keep track of variables
        symbolTable = {}
        # to keep track of scopes
        scopeDatabase = set()
        # for dfs
        stack: list[tuple(IRNode, str)] = [(root, root.filename)]

        while stack:
            payload = stack.pop()
            node: IRNode = payload[0]
            scope: str = payload[1]

            visited.add(node.id)
            visitedList.append(node.id)
            scopeDatabase.add(scope)

            # do the ting
            node.setDataFlowProps(scope, self.sources, self.sinks, self.sanitizers)
            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(node, visited, visitedList, scopeDatabase, symbolTable)
            
            controlId = uuid.uuid4().hex
            
            for child in node.astChildren:
                if not self.isIgnoredType(child):
                    if node.isControlStatement():
                        # assign controlId to differentiate scope between control branches
                        child.controlId = controlId
            stack.extend(reversed([(child, scope) for child in node.astChildren]))

    def createDataFlowTreeDFS(self, root: Node, filename: str) -> IRNode:
        projectId = uuid.uuid4().hex
        irRoot = IRJavascriptNode(root, filename, projectId)

        # to keep track of all visited nodes
        visited = set()
        # to keep track of order of visited nodes
        visitedList = []
        # to keep track of variables
        symbolTable = {}
        # to keep track of scopes
        scopeDatabase = set()
        # for dfs
        stack: list[tuple(IRNode, str)] = [(irRoot, filename)]

        while stack:
            payload = stack.pop()
            node: IRNode = payload[0]
            scope: str = payload[1]

            visited.add(node.id)
            visitedList.append(node.id)
            scopeDatabase.add(scope)

            # do the ting
            node.setDataFlowProps(scope, self.sources, self.sinks, self.sanitizers)
            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(node, visited, visitedList, scopeDatabase, symbolTable)
            
            controlId = uuid.uuid4().hex
            
            for child in node.node.children:
                if not self.isIgnoredType(child):
                    if node.type == "if_statement":
                        irChild = IRJavascriptNode(child, node.filename, node.projectId, controlId=controlId, parent=node)
                    else:
                        irChild = IRJavascriptNode(child, node.filename, node.projectId, parent=node)
                    node.astChildren.append(irChild)
            stack.extend(reversed([(child, scope) for child in node.astChildren]))
        
        return irRoot

    def setNodeDataFlowEdges(self, node: IRNode, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        # handle variable assignment and reassignment
        if node.isIdentifier() and node.isPartOfAssignment():
            key = (node.content, node.scope)
            # check node in left hand side
            if node.isInLeftHandSide():
                # reassignment of an existing variable
                if key in symbolTable:
                    dataType = "reassignment"
                    dfgParentId = symbolTable[key][-1]
                    node.addDataFlowEdge(dataType, None)
                    # register node id to symbol table
                    symbolTable[key].append(node.id)
                else:
                    # assignment of a new variable
                    dataType = "assignment"
                    node.addDataFlowEdge(dataType, None)
                    symbolTable[key] = [node.id]
            else:
                # reference of an existing variable as value of another variable
                dataType = "referenced"
                if key in symbolTable:
                    dfgParentId = symbolTable[key][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                if node.isInsideIfElseBranch():
                    self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType,  symbolTable)
                    self.connectDataFlowEdgeToInsideFromInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
                else:
                    self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)

        # handle value of an assignment but is not identifier
        if node.isInRightHandSide() and node.isPartOfAssignment():
            if node.isValueOfAssignment():
                identifier = node.node.prev_sibling.prev_sibling.text.decode("UTF-8")
                key = (identifier, node.scope)
                if key in symbolTable:
                    dfgParentId = symbolTable[key][-1]
                    dataType = "value"
                    node.addDataFlowEdge(dataType, dfgParentId)

        # handle variable called as argument in function
        if node.isIdentifier() and (node.isPartOfCallExpression() or node.isPartOfBinaryExpression()):
            key = (node.content, node.scope)
            dataType = "called"
            if node.isPartOfCallExpression():
                nodeCall = node.getCallExpression()
            else:
                nodeCall = node.getBinaryExpression()
            nodeCall.addDataFlowEdge(dataType, node.id)

            if key in symbolTable:
                dfgParentId = symbolTable[key][-1]
                node.addDataFlowEdge(dataType, dfgParentId)

            if node.isInsideIfElseBranch():
                self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
                self.connectDataFlowEdgeToInsideFromInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
            else:
                self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)

    def determineScopeNode(self, node: IRNode, prevScope: str) -> str:
        currScope = prevScope
        scopeIdentifiers = JAVASCRIPT_DATA_SCOPE_IDENTIFIERS
        controlScopeIdentifiers = JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS
        currentIdentifier = ""

        # add new scope for children if this node is class, function, module, and control branch
        if node.type in scopeIdentifiers:
            for child in node.node.children:
                # get the class, function, or module name
                if child.type == "identifier":
                    # store name to pass down to the children
                    currentIdentifier = child.text.decode("utf-8")
        # add new scope for children if this node is child of a control statement
        elif node.type in controlScopeIdentifiers and node.parent is not None and node.parent.isControlStatement():
            if node.controlId != None:
                currentIdentifier = f"{node.type}{node.controlId}"
            else:
                currentIdentifier = f"{node.type}{uuid.uuid4().hex}"

        if currentIdentifier != "":
            currScope += f"\{currentIdentifier}"

        return currScope
    
    def connectDataFlowEdgeToOutsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        for targetScope in scopeDatabase:
            targetDataScope = self.getDataScope(targetScope)
            currentDataScope = self.getDataScope(node.scope)

            if targetDataScope != currentDataScope:
                continue

            targetKey = (node.content, targetScope)
            # check previous key exists in symbol table
            # and check no key exists yet in current scope
            if targetKey in symbolTable and key not in symbolTable:
                dfgParentId = symbolTable[targetKey][-1]
                node.addDataFlowEdge(dataType, dfgParentId)

    def connectDataFlowEdgeToInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        # iterate through every scope registered
        currentDataScope = self.getDataScope(node.scope)
        for scope in scopeDatabase:
            if scope == None:
                continue

            targetDataScope = self.getDataScope(scope)
            if targetDataScope != currentDataScope:
                continue

            if not self.isControlScope(scope):
                continue

            controlKey = (node.content, scope)
            if controlKey in symbolTable:
                insideId = symbolTable[controlKey][-1]
            else:
                continue

            if key in symbolTable:
                outsideId = symbolTable[key][-1]
                outsideOrder = visitedList.index(outsideId)
            else:
                outsideOrder = -1

            insideOrder = visitedList.index(insideId)
            currentOrder = visitedList.index(node.id)

            # make sure last outside occurance of variable is BEFORE if statement OR there is no outside occurance
            # and make sure last inside occurance of variable is BEFORE current occurance
            if outsideOrder < insideOrder and insideOrder < currentOrder:
                dfgParentId = symbolTable[controlKey][-1]
                node.addDataFlowEdge(dataType, dfgParentId)
                # handle variable in argument list in function
                if node.isPartOfCallExpression():
                    nodeCall = node.getCallExpression()
                    nodeCall.addDataFlowEdge(dataType, node.id)

    # only for languages that don't have scopes in if else blocks
    # looking at you python
    def connectDataFlowEdgeToInsideFromInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        currentDataScope = self.getDataScope(node.scope)

        # iterate through every scope registered
        for scope in scopeDatabase:
            if scope == None:
                continue

            targetDataScope = self.getDataScope(node.scope)
            # check data scope is identical
            if targetDataScope != currentDataScope:
                continue

            targetGlobalScope, _, targetControlScope = scope.rpartition("\\")
            currentGlobalScope, _, currentControlScope = node.scope.rpartition("\\")

            # check both scope is inside control branch
            if not self.isControlScope(scope) or not self.isControlScope(node.scope):
                continue
            # check if-else id(s) to make sure scopes aren't from the same branch
            if self.getControlId(targetControlScope) == self.getControlId(currentControlScope):
                continue

            controlKey = (node.content, scope)
            outsideKey = (node.content, targetDataScope)
            if controlKey in symbolTable and outsideKey in symbolTable:
                outsideId = symbolTable[outsideKey][-1]
                insideId = symbolTable[controlKey][-1]
                outsideOrder = visitedList.index(outsideId)
                insideOrder = visitedList.index(insideId)
                currentOrder = visitedList.index(node.id)

                # make sure last outside occurance of variable is BEFORE if statement
                # and make sure last inside occurance of variable is BEFORE current occurance
                if outsideOrder < insideOrder and insideOrder < currentOrder:
                    dfgParentId = symbolTable[controlKey][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                    # handle variable in argument list in function
                    if node.isPartOfCallExpression():
                        nodeCall = node.getCallExpression()
                        nodeCall.addDataFlowEdge(dataType, node.id)
    
    def isControlScope(self, scope: str) -> bool:
        return len(scope.rpartition("\\")[2]) > 32 and scope.rpartition("\\")[2][:-32] in JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS
    
    def getControlId(self, scope: str) -> str:
        return scope[-32:] if self.isControlScope(scope) else ""