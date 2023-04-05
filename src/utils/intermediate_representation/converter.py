from tree_sitter import Node
from typing import Union
from utils.intermediate_representation.nodes import ASTNode
from uuid import uuid4
import csv

class IRConverter():
    def __init__(self) -> None:
        pass

    def createAstTree(self, root: Node) -> ASTNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        astRoot = ASTNode(root)

        queue: list[tuple(ASTNode, Union[ASTNode, None])] = [(root, None)]

        while len(queue) != 0:
            node, parent = queue.pop(0)

            if self.isIgnoredType(node):
                continue

            convertedNode = ASTNode(node, parent)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                astRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return astRoot

    # TODO: integrate with createAst if alr working
    def createCfgTree(self, root: ASTNode) -> ASTNode:
        queue = [(root, 0)]

        while len(queue) != 0:
            currNode, statementOrder = queue.pop(0)

            if statementOrder != 0:
                currNode.createCfgNode(statementOrder)
            
            statementOrder = 0
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

            # print("children assignment")
            # print(currNode.content)
            # print(currNode.node.children_by_field_name("assignment"))

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
    
    def createDfgTree(self, root: ASTNode):
        symbolTable = self.createSymbolTable(root)

        queue = [root]

        while len(queue) != 0:
            currNode = queue.pop(0)

            if currNode.id in symbolTable:
                dataProps = symbolTable[currNode.id]
                currNode.createDfgNode(dataProps["parent"], True, dataProps["type"], dataProps["scope"])
                
            for child in currNode.astChildren:
                queue.append(child)

    def printTree(self, node: ASTNode, depth=0):
        indent = ' ' * depth

        print(f'{indent}[{node.id}] {node.type} control?{node.controlFlowProps != None} : {node.content}')

        for child in node.astChildren:
            self.printTree(child, depth + 2)

    def exportAstToCsv(self, root: ASTNode):
        header = ['id', 'tree_sitter_id', 'type', 'content', 'parent_id', 'statement_order', 'dfg_parent_id']
        with open(f'./csv/{uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[ASTNode] = [root]

            while queue:
                node = queue.pop(0)

                statementOrder = node.controlFlowProps.statementOrder if node.controlFlowProps is not None else -1
                dfgParentId = node.dataFlowProps.dfgParentId if node.dataFlowProps is not None else -1
                row = [node.id, node.treeSitterId, node.type, node.content, node.parentId, statementOrder, dfgParentId]
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

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

        if node.type in ignoredList:
            return True
        
        return False