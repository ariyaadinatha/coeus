from tree_sitter import Node
from typing import Union
from utils.intermediate_representation.nodes import ASTNode
from uuid import uuid4
from pathlib import Path
import csv

class IRConverter():
    def __init__(self, sources, sinks, sanitizers, language: str) -> None:
        self.sources = sources
        self.sinks = sinks
        self.sanitizers = sanitizers
        self.language = language

    def createAstTree(self, root: Node, filename: str) -> ASTNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        astRoot = ASTNode(root, filename=filename)

        queue: list[tuple(ASTNode, Union[ASTNode, None])] = [(root, None)]

        while len(queue) != 0:
            node, parent = queue.pop(0)

            if self.isIgnoredType(node):
                continue

            convertedNode = ASTNode(node, filename, parent)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                astRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return astRoot

    def addControlFlowProps(self, root: ASTNode) -> ASTNode:
        queue = [(root, 0)]

        while len(queue) != 0:
            currNode, statementOrder = queue.pop(0)

            if statementOrder != 0:
                currNode.createCfgNode(statementOrder)
            
            statementOrder = 0
            # this handles the next statement relationship
            # only works for straight up line-by-line control flow
            # TODO: handle for, while, try, catch, etc. control
            for child in currNode.astChildren:
                if "statement" in child.type:
                    statementOrder += 1
                    queue.append((child, statementOrder))
                else:
                    queue.append((child, 0))

        return root

    def createSymbolTable(self, root: ASTNode) -> dict:
        # 1. check node with type assignment
        # 2. store left node as variable
        # 3. store right node as value
        # 4. store right node as variable if reassignment

        symbolTable = {}

        queue = [root]

        while len(queue) != 0:
            currNode = queue.pop(0)

            if currNode.parent is not None and currNode.parent.type == "assignment":
                # check variable declaration or not
                if currNode.type == "identifier":
                    if currNode.node.next_sibling is None:
                        symbolTable[currNode.id] = {
                                                    "parent": currNode.node.prev_sibling.id,
                                                    "scope": currNode.parent,
                                                    "type": "variable",
                                                    "is_reference": True,
                                                    "identifier": currNode.content
                                                    }
                    else:
                        symbolTable[currNode.id] = {
                                                    "parent": None,
                                                    "scope": currNode.parent,
                                                    "type": "reference",
                                                    "is_assignment": True,
                                                    "identifier": currNode.content
                                                    }
                
            for child in currNode.astChildren:
                queue.append(child)

        return symbolTable
    
    def addDataFlowEdges(self, root: ASTNode):
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
            currNode.isSink = self.isSink(currNode)
            currNode.scope = scope

            # add new scope for children if this node is class, function, module
            if currNode.type in scopeIdentifiers:
                for child in currNode.astChildren:
                    # get the class, function, or module name
                    if child.type == "identifier":
                        # store name to pass down to the children
                        currentIdentifier = child.content
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

            for child in currNode.astChildren:
                queue.append((child, scope))

    def createCompleteTree(self, root: Node, filename: str) -> ASTNode:
        astRoot = self.createAstTree(root, filename)
        self.addControlFlowProps(astRoot)
        self.addDataFlowEdges(astRoot)

        return astRoot

    def printTree(self, node: ASTNode, depth=0):
        indent = ' ' * depth

        print(f'{indent}{node}')

        for child in node.astChildren:
            self.printTree(child, depth + 2)

    # might need to separate ast, cfg and dfg export to three separate csv files
    # TODO: export cfg edges using separate function and csv file (see dfg for reference)
    def exportAstNodesToCsv(self, root: ASTNode):
        header = [
                'id', 
                'type', 
                'content', 
                'parent_id', 
                'statement_order', 
                'scope', 
                'is_source', 
                'is_sink', 
                'is_tainted'
                ]
        
        # setup file and folder
        basename = self.getExportBasename(root.scope)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_nodes.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[ASTNode] = [root]

            while queue:
                node = queue.pop(0)

                statementOrder = node.controlFlowEdges.statementOrder if node.controlFlowEdges is not None else -1
                row = [
                    node.id, 
                    node.type, 
                    node.content, 
                    node.parentId, 
                    statementOrder, 
                    node.scope, 
                    node.isSource,
                    node.isSink,
                    node.isTainted,
                    ]
                writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)

    def exportDfgEdgesToCsv(self, root: ASTNode):
        header = ['id', 'dfg_parent_id', 'data_type']

        # setup file and folder
        basename = self.getExportBasename(root.scope)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_edges.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[ASTNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.dataFlowEdges:
                    row = [node.id, edge.dfgParentId, edge.dataType]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)
    
    def exportCfgToCsv(self, root: ASTNode):
        header = ['id', 'statement_order']
        with open(f'./csv/{uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue = [root]

            while queue:
                node = queue.pop(0)

                row = [node.id, node.controlFlowEdges.statementOrder]
                writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)      

    def getSources(self, root: ASTNode):
        # 1. check node is source
        # 2. get node scope and identifier and store it

        queue = [root]

        while len(queue) != 0:
            currNode = queue.pop(0)

            if self.isSource(currNode):
                currNode.addDataFlowEdge(None, None, None, None)
                currNode.dataFlowEdges.isSource = True
                
            for child in currNode.astChildren:
                queue.append(child)

    def getExportBasename(self, filename: str) -> str:
        basename = filename.split(".")[1].replace("/", "-").replace("\\", "-")
        if basename[0] == "-":
            basename = basename[1:]
        
        return basename

    def isSource(self, node: ASTNode) -> bool:
        # TODO: handle different languages and keywords
        if node.content in self.sources:
            return True
        return False
    
    def isSink(self, node: ASTNode) -> bool:
        # TODO: handle different languages and keywords
        if node.content in self.sinks:
            return True
        return False

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

        if node.type in ignoredList:
            return True
        
        return False