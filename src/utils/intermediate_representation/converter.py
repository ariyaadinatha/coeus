from tree_sitter import Node
from typing import Union
from utils.intermediate_representation.nodes import ASTNode

class IRConverter():
    def __init__(self) -> None:
        pass

    def createAstTree(self, root: Node) -> ASTNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        astRoot = ASTNode(root)

        queue: list[tuple(Node, Union[ASTNode, None])] = [(root, None)]

        while queue:
            nodeAndParent = queue.pop(0)

            node, parent = nodeAndParent
            convertedNode = ASTNode(node, parent)

            if parent is not None:
                parent.astChildren.append(convertedNode)

            for child in nodeAndParent[0].children:
                queue.append((child, parent))

        return root

    def printTree(self, node: Node, depth=0):
        removedList = ['"', '=', '(', ')', '[', ']', ':']
        indent = ' ' * depth
        if node.type in removedList:
            return
        
        print(f'{indent}[{node.id}] {node.type} : {node.text.decode("utf-8") }')
        for child in node.children:
            self.printTree(child, depth + 2)

    # def traverseTree(self, node: Node, parent: Node, depth=0):
    #     removedList = ['"', '=', '(', ')', '[', ']', ':']
    #     indent = ' ' * depth
    #     if node.type in removedList:
    #         return
        
    #     astNode = ASTNode(node, parent)


    #     for child in node.children:
    #         self.traverseTree(child, node, depth + 2)

    def createCfg(self, root: ASTNode):
        #
        ignoredList = ['"', '=', '(', ')', '[', ']', ':']
        while type(node.id) is int:
            if node.type in ignoredList:
                continue




