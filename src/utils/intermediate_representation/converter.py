from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes import IRNode
import uuid
from pathlib import Path
import csv

class IRConverter():
    def __init__(self, sources, sinks, sanitizers) -> None:
        self.sources = sources
        self.sinks = sinks
        self.sanitizers = sanitizers

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
            if currNode.type == "if_statement" or currNode.type == "else_clause":
                for child in currNode.astChildren:
                    if child.type == "block":
                        blockNode = child
                        if len(blockNode.astChildren) != 0:
                            # connect if true statements with if statement
                            if currNode.type == "if_statement":
                                # !!!: depends on lower node
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.id)
                            # connect else statements with if statement
                            elif currNode.type == "else_clause":
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
            currNode.isSource = self.isSource(currNode)
            currNode.isTainted = self.isSource(currNode)
            currNode.isSink = self.isSink(currNode)
            currNode.isSanitizer = self.isSanitizer(currNode)
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

    def createCompleteTree(self, root: Node, filename: str) -> IRNode:
        irRoot = self.createAstTree(root, filename)
        self.addControlFlowEdgesToTree(irRoot)
        self.addDataFlowEdgesToTree(irRoot)

        return irRoot
    
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
    
    def createCompleteTreeDFS(self, root: Node, filename: str) -> IRNode:
        irRoot = self.createDataFlowTreeDFS(root, filename)
        self.addControlFlowEdgesToTree(irRoot)

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
                        node.addDataFlowEdge(dataType, dfgParentId)
                        # register node id to symbol table
                        symbolTable[key].append(node.id)
                    # assignment of a new variable
                    else:
                        dataType = "assignment"
                        node.addDataFlowEdge(dataType, None)
                        symbolTable[key] = [node.id]
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

    def printTree(self, node: IRNode, filter: Callable[[IRNode], bool], depth=0):
        indent = ' ' * depth

        if filter(node):
            print(f'{indent}{node}')
            # control flow info
            # for control in node.controlFlowEdges:
            #     print(f'{indent}[control] {control.cfgParentId} - {control.statementOrder}')

            # taint analysis info
            print(f'{indent}sink {node.isSink}')
            print(f'{indent}source {node.isSource}')
            print(f'{indent}sanitizer {node.isSanitizer}')

            # data flow info
            for data in node.dataFlowEdges:
                print(f'{indent}[data] {data.dfgParentId} - {data.dataType}')

        for child in node.astChildren:
            self.printTree(child, filter, depth + 2)

    def determineScopeNode(self, node: Node, prevScope: str):
        currScope = prevScope
        scopeIdentifiers = ("class_definition", "function_definition")

        # add new scope for children if this node is class, function, module
        if node.type in scopeIdentifiers:
            for child in node.node.children:
                # get the class, function, or module name
                if child.type == "identifier":
                    # store name to pass down to the children
                    currentIdentifier = child.text.decode("utf-8")
            currScope += f"\{currentIdentifier}"

        return currScope

    def exportAstNodesToCsv(self, root: IRNode, exportPath: str):
        header = [
                'id', 
                'type', 
                'content', 
                'parent_id', 
                'scope', 
                'location',
                'is_source', 
                'is_sink', 
                'is_tainted',
                'is_sanitizer',
                ]
        
        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_nodes.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                row = [
                    node.id, 
                    node.type, 
                    node.content, 
                    node.parentId, 
                    node.scope, 
                    node.location,
                    node.isSource,
                    node.isSink,
                    node.isTainted,
                    node.isSanitizer,
                    ]
                writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)

    def exportDfgEdgesToCsv(self, root: IRNode, exportPath: str):
        header = ['id', 'dfg_parent_id', 'data_type']

        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_dfg_edges.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.dataFlowEdges:
                    row = [node.id, edge.dfgParentId, edge.dataType]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)
    
    def exportCfgEdgesToCsv(self, root: IRNode, exportPath: str):
        header = ['id', 'cfg_parent_id', 'statement_order']

        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_cfg_edges.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.controlFlowEdges:
                    row = [node.id, edge.cfgParentId, edge.statementOrder]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)     
    
    def exportTreeToCsvFiles(self, root: IRNode, exportPath: str):
        self.exportAstNodesToCsv(root, exportPath)
        self.exportDfgEdgesToCsv(root, exportPath)
        self.exportCfgEdgesToCsv(root, exportPath)

    def getExportBasename(self, filename: str) -> str:
        if len(filename.split("\\")) >= 2:
            basename = filename.split("\\")[-1].replace("/", "-").replace("\\", "-")
            if basename[0] == "-":
                basename = basename[1:]
        
            return basename
        return filename

    def isSource(self, node: IRNode) -> bool:
        for source in self.sources:
            if source in node.content.lower():
                return True
        return False
    
    def isSink(self, node: IRNode) -> bool:
        for sink in self.sinks:
            if sink in node.content.lower():
                return True
        return False
    
    def isSanitizer(self, node: IRNode) -> bool:
        for sanitizer in self.sanitizers:
            if sanitizer in node.content.lower():
                return True
        return False

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '.', ',', '=', '(', ')', '[', ']', ':', '{', '}', 'comment']

        if node.type in ignoredList:
            return True
        
        return False