from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes import IRNode
import uuid

class IRConverter():
    def __init__(self, sources, sinks, sanitizers) -> None:
        self.sources = sources
        self.sinks = sinks
        self.sanitizers = sanitizers

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
        irRoot = IRNode(root, filename, projectId)

        queue: list[tuple(IRNode, Union[IRNode, None])] = [(root, None)]

        while len(queue) != 0:
            node, parent = queue.pop(0)

            if self.isIgnoredType(node):
                continue

            convertedNode = IRNode(node, filename, projectId, parent)

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
                if "statement" in child.type:
                    statementOrder += 1
                    queue.append((child, statementOrder, currCfgParent))
                    currCfgParent = child.id
                else:
                    queue.append((child, 0, None))
    
    def addDataFlowEdgesToTree(self, root: IRNode):
        queue = [(root, root.scope)]
        # symbol table to store variables as key and their node ids as value
        # key: (identifier, scope)
        # value: [ids]
        # scope to differentiate duplicate identifiers
        symbolTable = {}
        scopeIdentifiers = ("class_definition", "function_definition")

        while len(queue) != 0:
            currNode, scope = queue.pop(0)

            # set data flow properties
            currNode.isSource = currNode.checkIsSource()
            currNode.isTainted = currNode.checkIsSource()
            currNode.isSink = currNode.checkIsSink()
            currNode.isSanitizer = currNode.checkIsSanitizer()
            currNode.scope = scope

            # add new scope for children if this node is class, function, module
            if currNode.type in scopeIdentifiers:
                for child in currNode.node.children:
                    # get the class, function, or module name
                    if child.type == "identifier":
                        # store name to pass down to the children
                        currentIdentifier = child.text.decode("utf-8")
                scope += f"\{currentIdentifier}"
            
            # handle variable assignment and reassignment
            if currNode.type == "identifier" and currNode.parent.type == "assignment":
                key = (currNode.content, currNode.scope)
                if currNode.node.prev_sibling is None:
                    # reassignment of an existing variable
                    if key in symbolTable:
                        dataType = "reassignment"
                        dfgParentId = symbolTable[key][-1]
                        currNode.addDataFlowEdge(dataType, dfgParentId)
                        # register node id to symbol table
                        symbolTable[key].append(currNode.id)
                    # assignment of a new variable
                    else:
                        dataType = "assignment"
                        currNode.addDataFlowEdge(dataType, None)
                        symbolTable[key] = [currNode.id]
                else:
                    # reference of an existing variable as value of another variable
                    dataType = "referenced"
                    if key in symbolTable:
                        dfgParentId = symbolTable[key][-1]
                        currNode.addDataFlowEdge(dataType, dfgParentId)
            # handle value of an assignment but is not identifier
            if currNode.parent is not None and currNode.parent.type == "assignment":
                if currNode.node.prev_sibling is not None and currNode.node.prev_sibling.type == "=" and currNode.node.prev_sibling.prev_sibling.type == "identifier":
                    identifier = currNode.node.prev_sibling.prev_sibling.text.decode("UTF-8")
                    key = (identifier, currNode.scope)
                    if key in symbolTable:
                        dfgParentId = symbolTable[key][-1]
                        dataType = "value"
                        currNode.addDataFlowEdge(dataType, dfgParentId)

            # handle variable called as argument in function
            if currNode.type == "identifier" and currNode.parent.type != "assignment":
                key = (currNode.content, currNode.scope)
                if key in symbolTable:
                    dfgParentId = symbolTable[key][-1]
                    dataType = "called"
                    currNode.addDataFlowEdge(dataType, dfgParentId)
                    # handle variable in argument list in function
                    if currNode.parent.parent.type == "call":
                        currNode.parent.parent.addDataFlowEdge(dataType, currNode.id)
            
            for child in currNode.astChildren:
                queue.append((child, scope))
    
    def createDataFlowTree(self, root: Node, filename: str) -> IRNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        projectId = uuid.uuid4().hex
        irRoot = None
        symbolTable = {}

        queue: list[tuple(Node, Union[IRNode, None], str)] = [(root, None, filename)]

        while len(queue) != 0:
            node, parent, scope = queue.pop(0)

            if self.isIgnoredType(node):
                continue

            convertedNode = IRNode(node, filename, projectId, parent)
            convertedNode.setDataFlowProps(scope, self.sources, self.sanitizers, self.sinks)

            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(convertedNode, symbolTable)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                irRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode, scope))

        return irRoot
    
    def createDataFlowTreeDFS(self, root: Node, filename: str) -> IRNode:
        visited = set()
        symbolTable = {}

        projectId = uuid.uuid4().hex
        irRoot = IRNode(root, filename, projectId)

        self.dfs(irRoot, visited, symbolTable, filename)

        return irRoot
    
    def dfs(self, node: IRNode, visited, symbolTable, scope):
        visited.add(node.id)

        node.setDataFlowProps(scope, self.sources, self.sinks, self.sanitizers)
        scope = self.determineScopeNode(node, scope)
        self.setNodeDataFlowEdges(node, symbolTable)

        for child in node.node.children:
            if child.id not in visited:
                irChild = IRNode(child, node.filename, node.projectId, node)
                node.astChildren.append(irChild)
                self.dfs(irChild, visited, symbolTable, scope)

    def setNodeDataFlowEdges(self, node: IRNode, symbolTable):
            # handle variable assignment and reassignment
            if node.type == "identifier" and node.parent.type == "assignment":
                key = (node.content, node.scope)
                if node.node.prev_sibling is None:
                    # reassignment of an existing variable
                    if key in symbolTable:
                        dataType = "reassignment"
                        dfgParentId = symbolTable[key][-1]
                        # !!! : remove reassignment relationship temporarily
                        node.addDataFlowEdge(dataType, None)
                        # register node id to symbol table
                        symbolTable[key].append(node.id)
                    # assignment of a new variable
                    else:
                        dataType = "assignment"
                        node.addDataFlowEdge(dataType, None)
                        symbolTable[key] = [node.id]

                        if node.isInsideIfElseBranch():
                            
                else:
                    # reference of an existing variable as value of another variable
                    dataType = "referenced"
                    if key in symbolTable:
                        dfgParentId = symbolTable[key][-1]
                        node.addDataFlowEdge(dataType, dfgParentId)
            # handle value of an assignment but is not identifier
            if node.parent is not None and node.parent.type == "assignment":
                if node.node.prev_sibling is not None and node.node.prev_sibling.type == "=" and node.node.prev_sibling.prev_sibling.type == "identifier":
                    identifier = node.node.prev_sibling.prev_sibling.text.decode("UTF-8")
                    key = (identifier, node.scope)
                    if key in symbolTable:
                        dfgParentId = symbolTable[key][-1]
                        dataType = "value"
                        node.addDataFlowEdge(dataType, dfgParentId)

            # handle variable called as argument in function
            if node.type == "identifier" and node.parent.type != "assignment":
                key = (node.content, node.scope)
                if key in symbolTable:
                    dfgParentId = symbolTable[key][-1]
                    dataType = "called"
                    node.addDataFlowEdge(dataType, dfgParentId)
                    # handle variable in argument list in function
                    if node.parent.parent.type == "call":
                        node.parent.parent.addDataFlowEdge(dataType, node.id)

    def determineScopeNode(self, node: Node, prevScope: str):
        currScope = prevScope
        scopeIdentifiers = ("class_definition", "function_definition")
        controlScopeIdentifiers = ("else_clase", "elif_clause", "block")
        currentIdentifier = ""

        # add new scope for children if this node is class, function, module, and if-else branch
        if node.type in scopeIdentifiers:
            for child in node.node.children:
                # get the class, function, or module name
                if child.type == "identifier":
                    # store name to pass down to the children
                    currentIdentifier = child.text.decode("utf-8")
        elif node.type in controlScopeIdentifiers and node.parent.type == "if_statement":
                currentIdentifier = node.type

        if currentIdentifier != "":
            currScope += f"\{currentIdentifier}"

        return currScope

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '.', ',', '=', '(', ')', '[', ']', ':', '{', '}', 'comment']

        if node.type in ignoredList:
            return True
        
        return False