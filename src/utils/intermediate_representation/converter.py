from tree_sitter import Node
from typing import Union, Callable
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

    def addControlFlowEdges(self, root: ASTNode) -> ASTNode:
        queue: list[tuple(ASTNode, int, ASTNode)] = [(root, 0, None)]

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
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.id)
                            # connect else statements with if statement
                            elif currNode.type == "else_clause":
                                blockNode.astChildren[0].addControlFlowEdge(1, currNode.parentId)
            
            statementOrder = 0
            # handles the next statement relationship
            # TODO: handle for, while, try, catch, etc. control
            for child in currNode.astChildren:
                currCfgParent = None if currNode.type != "module" else currNode.id
                if "statement" in child.type:
                    statementOrder += 1
                    queue.append((child, statementOrder, currCfgParent))
                    currCfgParent = child.id
                else:
                    queue.append((child, 0, None))

        return root
    
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
        self.addControlFlowEdges(astRoot)
        self.addDataFlowEdges(astRoot)

        return astRoot

    def printTree(self, node: ASTNode, filter: Callable[[ASTNode], bool], depth=0):
        indent = ' ' * depth

        if filter(node):
            print(f'{indent}{node}')
            for control in node.controlFlowEdges:
                print(f'{indent}[control] {control.cfgParentId} - {control.statementOrder}')
            for data in node.dataFlowEdges:
                print(f'{indent}[data] {data.dfgParentId} - {data.dataType}')

        for child in node.astChildren:
            self.printTree(child, filter, depth + 2)

    # might need to separate ast, cfg and dfg export to three separate csv files
    # TODO: export cfg edges using separate function and csv file (see dfg for reference)
    def exportAstNodesToCsv(self, root: ASTNode):
        header = [
                'id', 
                'type', 
                'content', 
                'parent_id', 
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

                row = [
                    node.id, 
                    node.type, 
                    node.content, 
                    node.parentId, 
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

        with open(f'./csv/{basename}/{basename}_dfg_edges.csv', 'w+') as f:
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
    
    def exportCfgEdgesToCsv(self, root: ASTNode):
        header = ['id', 'cfg_parent_id', 'statement_order']

        # setup file and folder
        basename = self.getExportBasename(root.scope)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_cfg_edges.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[ASTNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.controlFlowEdges:
                    row = [node.id, edge.cfgParentId, edge.statementOrder]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)     
    
    def exportTreeToCsvFiles(self, root: ASTNode):
        self.exportAstNodesToCsv(root)
        self.exportDfgEdgesToCsv(root)
        self.exportCfgEdgesToCsv(root)

    def getExportBasename(self, filename: str) -> str:
        basename = filename.split(".")[1].replace("/", "-").replace("\\", "-")
        if basename[0] == "-":
            basename = basename[1:]
        
        return basename

    def isSource(self, node: ASTNode) -> bool:
        for source in self.sources:
            if source in node.content.lower():
                return True
        return False
    
    def isSink(self, node: ASTNode) -> bool:
        for sink in self.sinks:
            if sink in node.content.lower():
                return True
        return False

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

        if node.type in ignoredList:
            return True
        
        return False