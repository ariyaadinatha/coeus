from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.intermediate_representation.nodes.javascript import IRJavascriptNode
from utils.intermediate_representation.converter.converter import IRConverter
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS, PYTHON_DATA_SCOPE_IDENTIFIERS
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
        self.addDataFlowEdgesToTree(irRoot)

        return irRoot

    def createAstTree(self, root: Node, filename: str) -> IRNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        projectId = uuid.uuid4().hex
        irRoot = IRJavascriptNode(root, filename, projectId)

        queue: list[tuple(IRNode, Union[IRNode, None])] = [(root, None)]

        while len(queue) != 0:
            node, parent = queue.pop(0)

            if self.isIgnoredType(node):
                continue

            convertedNode = IRJavascriptNode(node, filename, projectId, parent)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                irRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return irRoot
    
    '''
        ide buat optimisasi graf
        gausa ada iterasi pertama yang cuman bikin ASTNode
        jadi bakal ngebuat ASTNode seiring jalan bikin CFG atau DFG
        tapi untuk ngehandle dependency ke lower node, kalau ada kejadian gitu
        bakal ngebuat lower node tersebut dan disimpan di hashset atau apa gt
        ntar tiap mau bikin ASTNode baru ngecek ke hashset tersebut dulu udah ada atau blm
        pro: satu iterasi
        cons: space yg dibutuhin bisa besar + perlu ngecek ke hash tiap ada isinya (tp harusnya ga lebih lama dr kl  iterasi gasih)
    '''

    '''
        ide lain buat optimisasi graf
        buat sedemikian rupa biar gaada dependency ke lower node
        jadi semua ngarah ke parent
    '''

    '''
        ide buat optimisasi speed I/O
        gausah pake neo4j kecuali kalo emang mau buat visualisasi (optional)
        jadi bikin algoritma taint analysis sendiri di python
        harusnya algoritmanya simpel cuman ngikutin data flow aja untuk setiap sink
        dan kalo ketemu sanitizer bakal berhenti
    '''

    '''
        buat masalah control flow prioritas terakhir
        sekarang fokus ke data flow
    '''

    def addControlFlowEdgesToTree(self, root: IRNode):
        queue: list[tuple(IRNode, int, IRNode)] = [(root, 0, None)]

        while len(queue) != 0:
            currNode, statementOrder, cfgParentId = queue.pop(0)

            if statementOrder != 0:
                currNode.addControlFlowEdge(statementOrder, cfgParentId)

            # handle if statement
            if currNode.type == "if_statement" or currNode.type == "else_clause" or currNode.type == "elif_clause":
                for child in currNode.astChildren:
                    if child.type == "block":
                        blockNode = child
                        if len(blockNode.astChildren) != 0:
                            # connect if true statements with if statement
                            if currNode.type == "if_statement":
                                # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.id)
                            # connect else statements with if statement
                            elif currNode.type == "else_clause" or currNode.type == "elif_clause":
                                # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.parentId)
            
            statementOrder = 0
            # handles the next statement relationship
            # TODO: handle for, while, try, catch, etc. control
            currCfgParent = None if currNode.type != "module" else currNode.id
            for child in currNode.astChildren:
                if "statement" in child.type or "declaration" in child.type:
                    statementOrder += 1
                    queue.append((child, statementOrder, currCfgParent))
                    currCfgParent = child.id
                else:
                    queue.append((child, 0, None))

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
        if node.isIdentifier() and not node.isPartOfAssignment():
            key = (node.content, node.scope)
            dataType = "called"
            if key in symbolTable:
                dfgParentId = symbolTable[key][-1]
                node.addDataFlowEdge(dataType, dfgParentId)
                # handle variable in argument list in function
                if node.parent.parent.type == "call":
                    node.parent.parent.addDataFlowEdge(dataType, node.id)
            if node.isInsideIfElseBranch():
                self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, symbolTable)
                self.connectDataFlowEdgeToInsideFromInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
            else:
                self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)

    def determineScopeNode(self, node: IRNode, prevScope: str) -> str:
        currScope = prevScope
        scopeIdentifiers = PYTHON_DATA_SCOPE_IDENTIFIERS
        controlScopeIdentifiers = PYTHON_CONTROL_SCOPE_IDENTIFIERS
        currentIdentifier = ""

        # add new scope for children if this node is class, function, module, and if-else branch
        if node.type in scopeIdentifiers:
            for child in node.node.children:
                # get the class, function, or module name
                if child.type == "identifier":
                    # store name to pass down to the children
                    currentIdentifier = child.text.decode("utf-8")
        elif node.type in controlScopeIdentifiers and node.parent is not None and node.parent.type == "if_statement":
                if node.controlId != None:
                    currentIdentifier = f"{node.type}{node.controlId}"
                else:
                    currentIdentifier = f"{node.type}{uuid.uuid4().hex}"

        if currentIdentifier != "":
            currScope += f"\{currentIdentifier}"

        return currScope
    
    def connectDataFlowEdgeToOutsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, symbolTable):
        previousScope = node.scope.rpartition("\\")[0]
        previousKey = (node.content, previousScope)
        # check previous key exists in symbol table
        # and check no key exists yet in current scope
        if previousKey in symbolTable and key not in symbolTable:
            dfgParentId = symbolTable[previousKey][-1]
            node.addDataFlowEdge(dataType, dfgParentId)

    def connectDataFlowEdgeToInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        # iterate through every scope registered
        for scope in scopeDatabase:
            if scope != None and scope.rpartition("\\")[0] == node.scope and self.isControlScope(scope):
                controlKey = (node.content, scope)
                if controlKey in symbolTable:
                    outsideId = symbolTable[key][-1]
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
                        if node.parent.parent.type == "call":
                            node.parent.parent.addDataFlowEdge(dataType, node.id)

    # only for languages that don't have scopes in if else blocks
    # looking at you python
    def connectDataFlowEdgeToInsideFromInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        # iterate through every scope registered
        for scope in scopeDatabase:
            if scope == None:
                continue

            targetGlobalScope, _, targetControlScope = scope.rpartition("\\")
            currentGlobalScope, _, currentControlScope = node.scope.rpartition("\\")

            # check global scope is identical
            if targetGlobalScope != currentGlobalScope:
                continue
            # check both scope is inside control branch
            if not self.isControlScope(scope) or not self.isControlScope(node.scope):
                continue
            # check if-else id(s) to make sure scopes aren't from the same branch
            if self.getControlId(targetControlScope) == self.getControlId(currentControlScope):
                continue

            controlKey = (node.content, scope)
            outsideKey = (node.content, targetGlobalScope)
            if controlKey in symbolTable:
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
                    if node.parent.parent.type == "call":
                        node.parent.parent.addDataFlowEdge(dataType, node.id)

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ("\"", ".", ",", "=", "==", "(", ")", "[", "]", ":", "{", "}", "comment")

        if node.type in ignoredList:
            return True
        
        return False
    
    def isControlScope(self, scope: str) -> bool:
        return len(scope.rpartition("\\")[2]) > 32 and scope.rpartition("\\")[2][:-32] in PYTHON_CONTROL_SCOPE_IDENTIFIERS
    
    def getControlId(self, scope: str) -> str:
        return scope[-32:] if self.isControlScope(scope) else ""