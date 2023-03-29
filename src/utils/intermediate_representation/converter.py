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

    def printTree(self, node: ASTNode, depth=0):
        indent = ' ' * depth

        print(f'{indent}[{node.id}] {node.type} : {node.content}')

        for child in node.astChildren:
            self.printTree(child, depth + 2)

    def exportToCsv(self, root: ASTNode):
        header = ['id', 'type', 'content', 'parent_id']
        with open(f'./csv/{uuid4().hex}.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue = [root]

            while queue:
                node = queue.pop(0)

                row = [node.id, node.type, node.content, node.parentId]
                writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

        if node.type in ignoredList:
            return True
        
        return False

    def createCfg(self, root: ASTNode):
        #
        ignoredList = ['"', '=', '(', ')', '[', ']', ':']
        while type(node.id) is int:
            if node.type in ignoredList:
                continue




