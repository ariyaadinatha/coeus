from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.intermediate_representation.nodes.irjavanode import IRJavaNode
from utils.intermediate_representation.converter.converter import IRConverter
from utils.constant.intermediate_representation import JAVA_CONTROL_SCOPE_IDENTIFIERS, JAVA_DATA_SCOPE_IDENTIFIERS
import uuid
from abc import ABC, abstractmethod

class IRJavaConverter(IRConverter):
    def __init__(self, sources, sinks, sanitizers) -> None:
        IRConverter.__init__(self, sources, sinks, sanitizers)

    def createAstTree(self, root: Node, filename: str) -> IRNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        projectId = uuid.uuid4().hex
        irRoot = IRJavaNode(root, filename, projectId)

        queue: list[tuple(IRNode, Union[IRNode, None])] = [(root, None)]

        while len(queue) != 0:
            currentPayload = queue.pop(0)
            node: Node = currentPayload[0]
            parent: IRNode = currentPayload[1]

            if self.isIgnoredType(node):
                continue

            convertedNode = IRJavaNode(node, filename, projectId, parent=parent)
            convertedNode.setDataFlowProps(self.sources, self.sinks, self.sanitizers)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                irRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return irRoot

    def addControlFlowEdgesToTree(self, root: IRJavaNode):
        queue: list[tuple(IRJavaNode, int, IRJavaNode)] = [(root, 0, None)]

        while len(queue) != 0:
            currPayload = queue.pop(0)
            currNode: IRJavaNode = currPayload[0]
            statementOrder: int = currPayload[1]
            cfgParentId: str = currPayload[2]

            if statementOrder != 0:
                currNode.addControlFlowEdge(statementOrder, cfgParentId)

            # handle if statement
            if currNode.isControlStatement() or currNode.isDivergingControlStatement() and not currNode.isElseIfBranch():
                for child in currNode.astChildren:
                    if child.type == "block":
                        blockNode = child
                        if len(blockNode.astChildren) != 0:
                            # connect if true statements with control statement and skip block node
                            if currNode.isControlStatement():
                            # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.id, f"{currNode.type}_child")
                            elif currNode.isDivergingControlStatement():
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.parentId, f"{currNode.type}_child")
            # handle else if
            elif currNode.isInElseIfBranch() and currNode.isFirstStatementInBlock():
                if currNode.parent.node.prev_sibling.type == "else":
                    controlType = "else_clause_child"
                else:
                    controlType = "else_if_clause_child"
                rootIfStatement: IRJavaNode = currNode.getRootIfStatement()
                currNode.addControlFlowEdge(1, rootIfStatement.id, controlType)
            
            statementOrder = 0
            # handles the next statement relationship
            currCfgParent = None if currNode.type != "program" else currNode.id
            for child in currNode.astChildren:
                if "statement" in child.type or "declaration" in child.type:
                    statementOrder += 1
                    queue.append((child, statementOrder, currCfgParent))
                    currCfgParent = child.id
                else:
                    queue.append((child, 0, None))

    def addDataFlowEdgesToTree(self, root: IRNode):
        # to keep track of all visited nodes
        visited = set()
        # to keep track of order of visited nodes
        visitedList = []
        # to keep track of variables
        symbolTable = {}
        # to keep track of block scoped variables
        blockScopedSymbolTable = {}
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
            node.scope = scope
            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(node, visited, visitedList, scopeDatabase, symbolTable, blockScopedSymbolTable)
            
            controlId = uuid.uuid4().hex
            
            for child in node.astChildren:
                if not self.isIgnoredType(child):
                    if node.isControlStatement():
                        # assign controlId to differentiate scope between control branches
                        child.controlId = controlId
            stack.extend(reversed([(child, scope) for child in node.astChildren]))

    def setNodeDataFlowEdges(self, node: IRNode, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict, blockScopedSymbolTable: dict):
        # handle variable assignment and reassignment
        if node.isIdentifier() and (node.isPartOfAssignment() or node.isArgumentOfAFunctionDefinition() or node.isPartOfReturnStatement()):
            key = (node.content, node.scope)
            # check node in left hand side
            if ((node.isInLeftHandSide() and node.isDirectlyInvolvedInAssignment()) or node.isArgumentOfAFunctionDefinition()) and not node.isValueOfAssignment():
                # reassignment of an existing variable
                if key in blockScopedSymbolTable:
                    dataType = "reassignment"
                    dfgParentId = blockScopedSymbolTable[key][-1]
                    node.addDataFlowEdge(dataType, None)
                    # register node id to symbol table
                    blockScopedSymbolTable[key].append(node.id)
                else:
                # assignment of a new variable
                    # handle block scope assignment
                    dataType = "assignment"
                    node.addDataFlowEdge(dataType, None)
                    blockScopedSymbolTable[key] = [node.id]
            else:
                # reference of an existing variable as value of another variable
                dataType = "referenced"
                if key in blockScopedSymbolTable:
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = blockScopedSymbolTable[key][-2] if len(blockScopedSymbolTable[key]) > 1 else None
                    else:
                        dfgParentId = blockScopedSymbolTable[key][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                if node.isInsideIfElseBranch():
                    self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable, blockScopedSymbolTable)
                else:
                    self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable, blockScopedSymbolTable)

        # handle value of an assignment
        if node.isPartOfAssignment() and not node.isPartOfCallExpression():
            if node.isValueOfAssignment():
                identifier = node.getIdentifierFromAssignment()
                key = (identifier, node.scope)
                if key in blockScopedSymbolTable:
                    dfgParentId = blockScopedSymbolTable[key][-1]
                    dataType = "value"
                    node.addDataFlowEdge(dataType, dfgParentId)

        # handle variable called as argument in function
        if (node.isIdentifier() or node.isAttribute() or node.isCallExpression()) and (node.isPartOfCallExpression() or node.isPartOfBinaryExpression()):
            key = (node.content, node.scope)
            dataType = "called"
            if node.isPartOfCallExpression():
                nodeCall = node.getCallExpression()
            else:
                nodeCall = node.getBinaryExpression()
            nodeCall.addDataFlowEdge(dataType, node.id)

            if key in blockScopedSymbolTable:
                # handle variable used for its own value
                # ex: test = test + "hahaha"
                if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                    dfgParentId = blockScopedSymbolTable[key][-2] if len(blockScopedSymbolTable[key]) > 1 else None
                else: 
                    dfgParentId = blockScopedSymbolTable[key][-1]
                    if node.isSourceOfMethodCall():
                        # connect back from function
                        node.addDataFlowEdge(dataType, nodeCall.id)

                        # register as new assignment
                        node.addDataFlowEdge("assignment", None)
                        blockScopedSymbolTable[key].append(node.id)
                node.addDataFlowEdge(dataType, dfgParentId)

            if node.isInsideIfElseBranch():
                self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable, blockScopedSymbolTable)
            else:
                self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable, blockScopedSymbolTable)
        
        # handle variable as argument in function call and connect to argument in function definition
        if node.isArgumentOfAFunctionCall():
            print('argument function call')
            print(node)
            functionAttributes = node.getFunctionAttributesFromFunctionCall()
            if len(functionAttributes) < 1:
                return
            functionName = functionAttributes[-1]
            print('function attr')
            print(functionAttributes)

            key = functionName
            if key in self.functionSymbolTable:
                parameterOrder = node.getOrderOfParametersInFunction()

                parameters = []
                for function in self.functionSymbolTable[key]:
                    if len(function['arguments']) <= parameterOrder: continue

                    parameter = function['arguments'][parameterOrder]
                    parameters.append(parameter)
                
                for parameter in parameters:
                    node.addDataFlowEdge("passed", parameter)

        # handle return from function
        # connect return to function call
        if node.isCallExpression():
            key = node.getIdentifierOfFunctionCall()
            returns = []
            
            if key in self.functionSymbolTable:
                for func in self.functionSymbolTable[key]:
                    returns.append(func['returns'])
            
            # flatten array
            returns = [item for sub_list in returns for item in sub_list]
            for returnId in returns:
                node.addDataFlowEdge('returned', returnId)

    def determineScopeNode(self, node: IRNode, prevScope: str) -> str:
        currScope = prevScope
        scopeIdentifiers = JAVA_DATA_SCOPE_IDENTIFIERS
        controlScopeIdentifiers = JAVA_CONTROL_SCOPE_IDENTIFIERS
        currentIdentifier = ""

        # add new scope for children if this node is class, function, module, and if-else branch
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
    
    def connectDataFlowEdgeToInsideFromInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        pass
    
    def connectDataFlowEdgeToOutsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict, blockScopedSymbolTable: list):
        for targetScope in scopeDatabase:
            if targetScope == node.scope:
                continue
            
            targetDataScope = self.getDataScope(targetScope)
            currentDataScope = self.getDataScope(node.scope)

            # for block scoped vars
            if not self.isInSameBlockScope(targetScope, node.scope) or targetDataScope != currentDataScope:
                continue

            targetKey = (node.content, targetScope)
            if self.isInSameBlockScope(targetScope, node.scope) and targetKey in blockScopedSymbolTable:
                if key not in blockScopedSymbolTable:
                    dfgParentId = blockScopedSymbolTable[targetKey][-1]
                    node.addDataFlowEdge(dataType, dfgParentId) 
                elif key in blockScopedSymbolTable and len(blockScopedSymbolTable[key]) <= 1:
                    # handle variable is used for its own assignment
                    '''
                    test = "test"
                    if True:
                        test = test.split("")
                    '''
                    '''
                    test = "test"
                    if True:
                        test = call(test)
                    '''
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = blockScopedSymbolTable[targetKey][-1]
                        node.addDataFlowEdge(dataType, dfgParentId)

    def connectDataFlowEdgeToInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict, blockScopedSymbolTable: dict):
        # iterate for block scope variables
        for blockScope in scopeDatabase:
            if not self.isInSameBlockScope(blockScope, node.scope):
                continue

            if not self.isControlScope(blockScope):
                continue

            controlKey = (node.content, blockScope)
            if controlKey in blockScopedSymbolTable:
                insideId = blockScopedSymbolTable[controlKey][-1]
            else:
                continue

            if key in blockScopedSymbolTable:
                outsideId = blockScopedSymbolTable[key][-1]
                outsideOrder = visitedList.index(outsideId)
            else:
                outsideOrder = -1

            insideOrder = visitedList.index(insideId)
            currentOrder = visitedList.index(node.id)

            # make sure last outside occurance of variable is BEFORE if statement OR there is no outside occurance
            # and make sure last inside occurance of variable is BEFORE current occurance
            if outsideOrder < insideOrder and insideOrder < currentOrder:
                dfgParentId = blockScopedSymbolTable[controlKey][-1]
                node.addDataFlowEdge(dataType, dfgParentId)
                # handle variable in argument list in function
                if node.isPartOfCallExpression():
                    nodeCall = node.getCallExpression()
                    nodeCall.addDataFlowEdge(dataType, node.id)

    def createDataFlowTreeDFS(self, root: Node, filename: str) -> IRNode:
        projectId = uuid.uuid4().hex
        irRoot = IRJavaNode(root, filename, projectId)

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
                        irChild = IRJavaNode(child, node.filename, node.projectId, controlId=controlId, parent=node)
                    else:
                        irChild = IRJavaNode(child, node.filename, node.projectId, parent=node)
                    node.astChildren.append(irChild)
            stack.extend(reversed([(child, scope) for child in node.astChildren]))
        
        return irRoot
    
    def isControlScope(self, scope: str) -> bool:
        return len(scope.rpartition("\\")[2]) > 32 and scope.rpartition("\\")[2][:-32] in JAVA_CONTROL_SCOPE_IDENTIFIERS
    
    def getControlId(self, scope: str) -> str:
        return scope[-32:] if self.isControlScope(scope) else ""