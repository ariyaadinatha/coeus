from tree_sitter import Node
from typing import Union
from utils.intermediate_representation.nodes import ASTNode
from uuid import uuid4
import csv

class IRConverter():
    def __init__(self) -> None:
        pass

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
    
    def addScope(self, root: ASTNode):
        queue = [(root, root.dataFlowProps.scope)]
        # TODO: create symbol table while initializing scope
        symbolTable = {}
        scopeIdentifiers = ("class_definition", "function_definition")

        while len(queue) != 0:
            currNode, scope = queue.pop(0)

            isSource = self.isSource(currNode)
            isSink = self.isSink(currNode)
            currNode.createDfgNode(scope, isSource, isSink, None)

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
                key = (currNode.content, currNode.dataFlowProps.scope)
                if currNode.node.prev_sibling is None:
                    if key in symbolTable:
                        currNode.dataFlowProps.dataType = "reassignment"
                        currNode.dataFlowProps.dfgParentId = symbolTable[key][-1]
                        symbolTable[key].append(currNode.id)
                    else:
                        currNode.dataFlowProps.dataType = "assignment"
                        symbolTable[key] = [currNode.id]
                else:
                    currNode.dataFlowProps.dataType = "referenced"
                    if key in symbolTable:
                        currNode.dataFlowProps.dfgParentId = symbolTable[key][-1]
            # handle value of an assignment but is not identifier
            elif currNode.parent is not None and currNode.parent.type == "assignment":
                if currNode.node.prev_sibling is not None and currNode.node.prev_sibling.type == "=" and currNode.node.prev_sibling.prev_sibling.type == "identifier":
                    identifier = currNode.node.prev_sibling.prev_sibling.text.decode("UTF-8")
                    key = (identifier, currNode.dataFlowProps.scope)
                    if key in symbolTable:
                        currNode.dataFlowProps.dfgParentId = symbolTable[key][-1]
                        currNode.dataFlowProps.dataType = "value"

            for child in currNode.astChildren:
                queue.append((child, scope))
    
    def addDataFlowEdges(self, root: ASTNode):
        # only iterate through source node
        queue = [root]

        while len(queue) != 0:
            pass

    def createCompleteTree(self, root: Node, filename: str) -> ASTNode:
        astRoot = self.createAstTree(root, filename)
        self.addControlFlowProps(astRoot)
        self.addScope(astRoot)

        return astRoot

    def printTree(self, node: ASTNode, depth=0):
        indent = ' ' * depth

        print(f'{indent}{node}')

        for child in node.astChildren:
            self.printTree(child, depth + 2)

    # might need to separate ast, cfg and dfg export to three separate csv files
    def exportAstToCsv(self, root: ASTNode):
        header = ['id', 'type', 'content', 'parent_id', 'statement_order', 'dfg_parent_id', 'scope', 'data_type', 'is_source']
        with open(f'./csv/{uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[ASTNode] = [root]

            while queue:
                node = queue.pop(0)

                statementOrder = node.controlFlowProps.statementOrder if node.controlFlowProps is not None else -1
                dfgParentId = node.dataFlowProps.dfgParentId if node.dataFlowProps is not None else -1
                row = [node.id, node.type, node.content, node.parentId, statementOrder, dfgParentId, node.dataFlowProps.scope, node.dataFlowProps.dataType, node.dataFlowProps.isSource]
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

                row = [node.id, node.controlFlowProps.statementOrder]
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
                currNode.createDfgNode(None, None, None, None)
                currNode.dataFlowProps.isSource = True
                
            for child in currNode.astChildren:
                queue.append(child)

    def isSource(self, node: ASTNode) -> bool:
        # TODO: handle different languages and keywords
        keywords = set("input()")

        if node.content in keywords:
            return True
        
        return False
    
    def isSink(self, node: ASTNode) -> bool:
        # TODO: handle different languages and keywords
        keywords = set("cursor.execute")
        
        if node.content in keywords:
            return True
        
        return False

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

        if node.type in ignoredList:
            return True
        
        return False