'''
python
'''
PYTHON_CONTROL_SCOPE_IDENTIFIERS = ("block", "elif_clause", "else_clause", "except_clause", "finally_clause")
PYTHON_CONTROL_STATEMENTS = ("if_statement", "for_statement", "while_statement", "try_statement")
PYTHON_DIVERGE_CONTROL_STATEMENTS = ("elif_clause", "else_clause", "except_clause", "finally_clause")
PYTHON_DATA_SCOPE_IDENTIFIERS = ("class_definition", "function_definition")

'''
javascript
'''
JAVASCRIPT_CONTROL_SCOPE_IDENTIFIERS = ("statement_block", "elif_clause", "else_clause")

'''
php
'''
PHP_CONTROL_SCOPE_IDENTIFIERS = ("compound_statement", "else_if_clause", "else_clause", "catch_clause")
PHP_CONTROL_STATEMENTS = ("if_statement", "for_statement", "foreach_statement", "while_statement", "try_statement")
PHP_DIVERGE_CONTROL_STATEMENTS = ("compound_statement", "else_if_clause", "else_clause", "catch_clause")
PHP_DATA_SCOPE_IDENTIFIERS = ("function_definition", "class_declaration")

'''
java
'''
JAVA_CONTROL_SCOPE_IDENTIFIERS = ("block", "elif_clause", "else_clause")
JAVA_CONTROL_STATEMENTS = ("if_statement", "for_statement", "while_statement", "try_statement")
JAVA_DIVERGE_CONTROL_STATEMENTS = ("else_clause")
JAVA_DATA_SCOPE_IDENTIFIERS = ("class_declaration", "method_declaration")