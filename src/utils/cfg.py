import tree_sitter
import networkx as nx
import matplotlib.pyplot as plt

class Converter:
    def __init__(self):
        pass

    def get_basic_blocks(self, node):
        # Helper function to get the basic blocks from an AST node
        basic_blocks = []
        if node.type == 'if_statement':
            basic_blocks.append(node.children[2])
            basic_blocks.append(node.children[4])
        elif node.type == 'for_statement':
            basic_blocks.append(node.children[3])
        elif node.type == 'while_statement':
            basic_blocks.append(node.children[2])
        else:
            basic_blocks.append(node)
        return basic_blocks

    def ast_to_cfg(self, ast_root):
        # Create a directed graph to represent the CFG
        graph = nx.DiGraph()

        # Add the basic blocks to the graph as nodes
        for node in ast_root.walk():
            blocks = self.get_basic_blocks(node)
            for block in blocks:
                graph.add_nodes_from(block)

        # Add edges to represent the flow of control
        for node in ast_root.walk():
            if node.type == 'if_statement':
                blocks = self.get_basic_blocks(node)
                graph.add_edges_from(zip(blocks[:-1], blocks[1:]))
            elif node.type == 'for_statement':
                blocks = self.get_basic_blocks(node)
                graph.add_edges_from(zip(blocks[:-1], blocks[1:]))
            elif node.type == 'while_statement':
                blocks = self.get_basic_blocks(node)
                graph.add_edges_from(zip(blocks[:-1], blocks[1:]))

        return graph
    
    def drawGraph(self, graph):
        nx.draw(graph, with_labels=True)
        plt.show()


# Example usage
# parser = tree_sitter.Parser()
# language = parser.get_language('python')
# code = """
# def factorial(n):
#     if n == 0:
#         return 1
#     else:
#         return n * factorial(n - 1)
# """
# tree = parser.parse(language, code)
# ast_root = tree.root_node
# cfg = ast_to_cfg(ast_root)
