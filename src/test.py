from tree_sitter import Language, Parser



Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',
  # Include one or more languages
  [
    'vendor/tree-sitter-java',
    'vendor/tree-sitter-php',
    'vendor/tree-sitter-javascript',
    'vendor/tree-sitter-python'
  ]
)

language = Language('build/my-languages.so', "python")
parser = Parser()
parser.set_language(language)


# Define some Python code to parse
code = """
hallo = 'qwe'

if hallo == '123':
    this = 2
    
"""

tree = parser.parse(bytes(code, "utf8"))
rootNode = tree.root_node

# Traverse the syntax tree
def traverse_tree(node):
    if node.type == 'assignment':
        # Get the variable name
        # print(node.children)
        var_name_node = node.children[0]
        var_name = code[var_name_node.start_byte:var_name_node.end_byte]
        print(f"Variable name: {var_name}")
        # Get the variable value
        var_value_node = node.children[1]
        var_value = code[var_value_node.start_byte:var_value_node.end_byte]
        print(f"Variable value: {var_value}")
    for child in node.children:
        traverse_tree(child)

traverse_tree(tree.root_node)
