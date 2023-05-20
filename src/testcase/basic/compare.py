import ast
import astor
import tree_sitter
from tree_sitter import Language

# Load the Python language and parse the Python code
Language.build_library(
    # Store the library in the `tree-sitter` subdirectory of the current directory
    'tree-sitter'
    # Include one or more languages
).generate_library('Python')

python_code = '''
intList = [4,1,6,5,3,2]
maxNum = -1

# find biggest int
for i in intList:
    if i > maxNum:
        maxNum = i

print(maxNum)
'''

python_ast = ast.parse(python_code)

# Load the Tree Sitter parser and parse the same Python code
parser = tree_sitter.Parser()
parser.set_language(Language('tree-sitter-Python'))

tree_sitter_code = '''
intList = [4,1,6,5,3,2]
maxNum = -1

# find biggest int
for i in intList:
    if i > maxNum:
        maxNum = i

print(maxNum)
'''

tree_sitter_tree = parser.parse(bytes(tree_sitter_code, 'utf8'))

# Compare the Python AST and Tree Sitter AST
python_code_from_ast = astor.to_source(python_ast)
tree_sitter_code_from_ast = tree_sitter_tree.root_node.pretty().strip()

if python_code_from_ast == tree_sitter_code_from_ast:
    print("The ASTs match")
else:
    print("The ASTs do not match")
