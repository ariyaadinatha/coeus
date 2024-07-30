from tree_sitter import Node
from typing import Union, Callable
from utils.intermediate_representation.nodes.nodes import IRNode
from utils.intermediate_representation.nodes.irpythonnode import IRPythonNode, FlaskLoginRequired
from utils.intermediate_representation.converter.converter import IRConverter
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS, PYTHON_DATA_SCOPE_IDENTIFIERS
import uuid
from abc import ABC, abstractmethod
import re

class IRPythonConverter(IRConverter):
    def __init__(self) -> None:
        IRConverter.__init__(self)
        self.decorators: list[tuple[str, IRNode]] = []
        self.callStmtList: list[tuple[str, IRNode]] = []
        self.functions: dict[str: IRNode] = {}

    def createAstTree(self, root: Node, filename: str) -> IRNode:
        # iterate through root until the end using BFS
        # create new AST node for each tree-sitter node

        projectId = uuid.uuid4().hex
        irRoot = IRPythonNode(root, filename, projectId)

        queue: list[tuple(IRNode, Union[IRNode, None])] = [(root, None)]

        while len(queue) != 0:
            currentPayload = queue.pop(0)
            node: Node = currentPayload[0]
            parent: IRNode = currentPayload[1]

            if self.isIgnoredType(node):
                continue

            convertedNode = IRPythonNode(node, filename, projectId, parent=parent)

            # add current node as child to parent node
            # else set root node
            if parent is not None:
                parent.astChildren.append(convertedNode)
            else:
                irRoot = convertedNode

            for child in node.children:
                queue.append((child, convertedNode))

        return irRoot
    
    # bagian Andrew
    # === BEGIN ===

    # Routes/Endpoints
    def identifyEndpoints(self, root: IRNode) -> list[IRNode]:
        
        queue : list[IRNode] = [root]
        endpointList : list[IRNode] = []
        
        while len(queue) != 0:
            
            node = queue.pop(0)

            if node.isEndpointStatement():
                node.isEndpoint = True
                endpointList.append(node)

            for ch in node.astChildren:
                queue.append(ch)
        
        return endpointList
    
    def identifyStops(self, root: IRNode, stopWords):
        queue: list[IRNode] = [root]
        
        while len(queue) != 0:
            node = queue.pop(0)
            c1 = (node.type == "expression_statement" or node.type == "return_statement") and node.astChildren[0].type != "string"
            c2 = False
            for word in stopWords:
                if word in node.content:
                    c2 = True
                    break

            if c1 and c2:
                node.isStop = True
            
            for ch in node.astChildren:
                queue.append(ch)
    
    def identifyMiddleware(self, root: IRNode, builtins: list[str]):
        queue: list[IRNode] = [root]
        
        while len(queue) != 0:
            node = queue.pop(0)
            c1 = node.type == "decorator"
            c2 = not re.match(r"(.*?).route", node.content)
            if c1 and c2:
                
                node.isMiddleware = True
                iden = node.astChildren[1]
                if iden.content not in builtins:
                    self.decorators.append((iden.content, node))
                else:    
                    node.isBuiltin = True
                    bi = FlaskLoginRequired("user", iden.content)
                    node.builtin = bi
                
            
            for ch in node.astChildren:
                queue.append(ch)
    
    def identifyFunctions(self, root: IRNode):
        queue: list[IRNode] = [root]
        
        while len(queue) != 0:
            node = queue.pop(0)

            if node.isFunctionDefinition():
                node.isCall = True
                iden = node.astChildren[1].content
                self.functions[iden] = node
            
            for ch in node.astChildren:
                queue.append(ch)


    # parse comparison
    def defineComparison(self, node: IRNode):
        # handle call and identifier
        variable = ""
        value = ""
        operator = ""

        if node.type == "identifier" or node.type == "call":
            variable = node.content
            value = "True"
            operator = "=="

        #TODO: handle boolean operator
        if node.type == "boolean_operator":
            return
        
        # handle comparison operator
        if node.type == "comparison_operator":
            variable = node.astChildren[0].content
            valueNode = node.astChildren[-1]
            value = node.astChildren[-1].content
            operator = "=="

            for child in node.astChildren:
                if child.type == "is":
                    operator = "is"
                if child.type == "is not":
                    operator = "is not"

            # string
            if valueNode.type == "string":
                value = valueNode.astChildren[1].content

        node.addComparison(variable, value, operator)
        

    # Control Flow
    def addControlFlowEdgesToTree(self, root: IRNode):
        # list all childs
        stmtList, defnList = self.parseBlocks(root)

        # parse each definitions
        for defn in defnList:
            self.parseDefinitions(defn)

        # parse each statements (if any)
        n_stmtList = len(stmtList)
        if n_stmtList > 0:
            stmtList.append(None)
            for i in range(n_stmtList):
                currStmt = stmtList[i]
                nextStmt = stmtList[i + 1]
                self.parseStatements(currStmt, nextStmt)

    def parseBlocks(self, node: IRNode):
        stmtList: list[IRNode] = []
        defList: list[IRNode] = []
        
        for child in node.astChildren:
            if "statement" in child.type:
                stmtList.append(child)
            elif "definition" in child.type:
                defList.append(child)
        
        return stmtList, defList

    # Definitions (function_definition, decorated_definition)
    def parseDefinitions(self, node: IRNode):
        if node.type == "function_definition":
            self.handleFunctionDefinitions(node)
        if node.type == "decorated_definition":
            self.handleDecoratedDefinitions(node)

    def handleFunctionDefinitions(self, node: IRNode):
        node.isCall = True
        nodeBlock = None
        for child in node.astChildren:
            if child.type == "block":
                nodeBlock = child

        nodeStmtList, nodeDefList = self.parseBlocks(nodeBlock)

        # parse each definitions
        for defn in nodeDefList:
            self.parseDefinitions(defn)

        node.addControlFlowEdge(nodeStmtList[0], nodeStmtList[0].id)
        nodeStmtList.append(None)
        for i in range(len(nodeStmtList) - 1):
            self.parseStatements(nodeStmtList[i], nodeStmtList[i+1])

    def handleDecoratedDefinitions(self, node: IRNode):
        child: list[IRNode] = []
        for ch in node.astChildren:
            child.append(ch)
        node.addControlFlowEdge(child[0], child[0].id)
        for i in range(len(child) - 1):
            child[i].addControlFlowEdge(child[i+1], child[i+1].id)
        
        self.handleFunctionDefinitions(child[-1])
        

    # Statements (expression_statement, if_statement, while_statement, for_statement, try_statement, return_statement)
    def parseStatements(self, curr: IRNode, next: IRNode):
        if curr.type == "if_statement":
            self.handleIfStatement(curr, next)
        elif curr.type == "try_statement":
            self.handleTryStatement(curr, next)
        elif curr.type == "return_statement":
            self.handleReturnStatement(curr, next)
        else:
            self.handleNextStatement(curr, next)

    def handleIfStatement(self, curr: IRNode, next: IRNode):
        condition: IRNode = None
        ifBlock: IRNode = None
        elifClauses: list[IRNode] = []
        elseBlock: IRNode = None
        for child in curr.astChildren:
            if "operator" in child.type or child.type == "identifier" or child.type == "call":
                condition = child
            if child.type == "block":
                ifBlock = child
            if child.type == "elif_clause":
                elifClauses.append(child)
            if child.type == "else_clause":
                elseBlock = child.astChildren[1]

        condition.isCheck = True
        self.defineComparison(condition)

        curr.addControlFlowEdge(condition, condition.id, "next_statement")
        
        insideIfBlockStmtList, insideIfBlockDefList = self.parseBlocks(ifBlock)
        insideIfBlockStmtList.append(next)
        condition.addControlFlowEdge(insideIfBlockStmtList[0], insideIfBlockStmtList[0].id, "next_statement_if_true")
        for i in range(len(insideIfBlockStmtList) - 1):
            self.parseStatements(insideIfBlockStmtList[i], insideIfBlockStmtList[i+1])

        if len(elifClauses) > 0:
            for i in range(len(elifClauses)):
                elifCondition: IRNode = elifClauses[i].astChildren[1]
                insideElifIfBlockStmtList, insideElifIfBlockDefList = self.parseBlocks(elifClauses[i].astChildren[2])
                insideElifIfBlockStmtList.append(next)
                elifCondition.addControlFlowEdge(insideElifIfBlockStmtList[0], insideElifIfBlockStmtList[0].id, "next_statement_if_true")
                for i in range(len(insideElifIfBlockStmtList) - 1):
                    self.parseStatements(insideElifIfBlockStmtList[i], insideElifIfBlockStmtList[i+1])
                
                condition.addControlFlowEdge(elifCondition, elifCondition.id, "next_statement_if_false")
                condition = elifCondition
                condition.isCheck = True
                self.defineComparison(condition)

        if elseBlock is not None:
            insideElseBlockStmtList, insideElseBlockDefList = self.parseBlocks(elseBlock)
            insideElseBlockStmtList.append(next)
            condition.addControlFlowEdge(insideElseBlockStmtList[0], insideElseBlockStmtList[0].id, "next_statement_if_false")
            for i in range(len(insideElseBlockStmtList) - 1):
                self.parseStatements(insideElseBlockStmtList[i], insideElseBlockStmtList[i+1])
        else:
            self.parseStatements(condition, next)

    def handleTryStatement(self, curr: IRNode, next: IRNode):
        tryBlock: IRNode = None
        elseBlock: IRNode = None
        finallyBlock: IRNode = None
        for child in curr.astChildren:
            if child.type == "block":
                tryBlock = child
            elif child.type == "else_clause":
                elseBlock = child.astChildren[1]
            elif child.type == "finally_clause":
                finallyBlock = child.astChildren[1]
        
        stmt: list[IRNode] = []
        
        insideTryBlockStmtList, _ = self.parseBlocks(tryBlock)
        stmt.extend(insideTryBlockStmtList)

        curr.addControlFlowEdge(stmt[0], stmt[0].id)
        
        if elseBlock is not None:
            insideElseBlockStmtList, _ = self.parseBlocks(elseBlock)
            stmt.extend(insideElseBlockStmtList)

        if finallyBlock is not None:
            insideFinallyBlockStmtList, _ = self.parseBlocks(finallyBlock)
            stmt.extend(insideFinallyBlockStmtList)
        
        stmt.append(next)
        for i in range(len(stmt) - 1):
            self.parseStatements(stmt[i], stmt[i+1])

    #TODO: while statement, for statement
    def handleWhileStatement(self, curr: IRNode, next: IRNode):
        pass

    def handleForStatement(self, curr:IRNode, next: IRNode):
        pass

    def handleReturnStatement(self, curr: IRNode, next: IRNode):
        res = curr.isStatementWithCall()
        if res[0] == True:
            callIdentifier = res[1]
            self.callStmtList.append((callIdentifier, curr))

    def handleNextStatement(self, curr: IRNode, next: IRNode):
        res = curr.isStatementWithCall()
        if res[0] == True:
            callIdentifier = res[1]
            self.callStmtList.append((callIdentifier, curr))
        
        if next != None:
            curr.addControlFlowEdge(next, next.id, "next_statement")


    # Call
    def addCallEdgesToTree(self):
        # from decorators
        for deco in self.decorators:
            if deco[0] in self.functions:
                funcNode = self.functions[deco[0]]
                funcId = funcNode.id
                deco[1].addCallEdge(funcNode, funcId)

        # from statements
        for stmt in self.callStmtList:
            if stmt[0] in self.functions:
                funcNode = self.functions[stmt[0]]
                funcId = funcNode.id
                stmt[1].addCallEdge(funcNode, funcId)

    # === END ===

    def addDataFlowEdgesToTree(self, root: IRNode):
        # to keep track of all visited nodes
        visited = set()
        # to keep track of order of visited nodes
        visitedList = []
        # to keep track of variables
        symbolTable = {}
        # to keep track of import statement
        importTable = {}
        # to keep track of scopes
        scopeDatabase = set()
        # for dfs
        stack: list[tuple(IRNode, str)] = [(root, root.filename)]

        while stack:
            payload = stack.pop()
            node: IRNode = payload[0]
            scope: str = payload[1]

            visited.add(node.id)
            visitedList.append(node.id)
            scopeDatabase.add(scope)

            # do the ting
            node.scope = scope
            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(node, visited, visitedList, scopeDatabase, symbolTable, importTable)
            
            controlId = uuid.uuid4().hex
            
            for child in node.astChildren:
                if not self.isIgnoredType(child):
                    if node.isControlStatement():
                        # assign controlId to differentiate scope between control branches
                        child.controlId = controlId
            stack.extend(reversed([(child, scope) for child in node.astChildren]))

    def saveImportOrigin(self, node: IRNode, importTable: dict):
        if node.isImportStatement():
            name, importOrigin = node.getImportOriginAndName()
            importTable[name] = importOrigin

    def setNodeDataFlowEdges(self, node: IRNode, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict, importTable: dict):
        # handle variable assignment and reassignment
        if node.isIdentifier() and (node.isPartOfAssignment() or node.isArgumentOfAFunctionDefinition() or node.isPartOfReturnStatement()):
            key = (node.content, node.scope)
            # check node in left hand side
            if ((node.isInLeftHandSide() and node.isDirectlyInvolvedInAssignment()) or node.isPartOfPatternAssignment() or node.isArgumentOfAFunctionDefinition()) and not node.isValueOfAssignment():
                # reassignment of an existing variable
                if key in symbolTable:
                    dataType = "reassignment"
                    node.addDataFlowEdge(dataType, None)
                    # register node id to symbol table
                    symbolTable[key].append(node.id)
                else:
                    # assignment of a new variable
                    dataType = "assignment"
                    node.addDataFlowEdge(dataType, None)
                    symbolTable[key] = [node.id]
            else:
                # reference of an existing variable as value of another variable
                dataType = "referenced"
                if key in symbolTable:
                    # handle variable used for its own value
                    # ex: test = test + "hahaha"
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = symbolTable[key][-2] if len(symbolTable[key]) > 1 else None
                    else:
                        dfgParentId = symbolTable[key][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                if node.isInsideIfElseBranch():
                    self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
                    self.connectDataFlowEdgeToInsideFromInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
                else:
                    self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)

        # handle value of an assignment
        if node.isPartOfAssignment() and not node.isPartOfCallExpression():
            if node.isValueOfAssignment():
                # handle standard assignment and destructuring assignment
                identifier = [node.getIdentifierFromAssignment()] if not node.isPartOfPatternAssignment() else node.getIdentifiersFromPatternAssignment()

                for id in identifier:
                    key = (id, node.scope)
                    if key in symbolTable:
                        dfgParentId = symbolTable[key][-1]
                        dataType = "value"
                        node.addDataFlowEdge(dataType, dfgParentId)

        # handle variable called as argument in function
        if (node.isIdentifier() or node.isAttribute() or node.isCallExpression()) and node.isPartOfCallExpression():
            key = (node.content, node.scope)
            dataType = "called"

            # connect identifier with function call to describe argument
            nodeCall = node.getCallExpression()
            nodeCall.addDataFlowEdge(dataType, node.id)

            if key in symbolTable:
                # handle variable used for its own value
                # ex: test = test + "hahaha"
                if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                    dfgParentId = symbolTable[key][-2] if len(symbolTable[key]) > 1 else None
                else:
                    dfgParentId = symbolTable[key][-1]
                node.addDataFlowEdge(dataType, dfgParentId)

            if node.isInsideIfElseBranch():
                self.connectDataFlowEdgeToOutsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
                self.connectDataFlowEdgeToInsideFromInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)
            else:
                self.connectDataFlowEdgeToInsideIfElseBranch(node, key, dataType, visited, visitedList, scopeDatabase, symbolTable)

        # handle variable as argument in function call and connect to argument in function definition
        if node.isArgumentOfAFunctionCall():
            functionAttributes = node.getFunctionAttributesFromFunctionCall()

            if len(functionAttributes) < 1:
                return
            functionName = functionAttributes[-1]

            key = functionName
            if key in self.functionSymbolTable:
                parameterOrder = node.getOrderOfParametersInFunction()

                parameters = []
                for function in self.functionSymbolTable[key]:
                    if len(function['arguments']) <= parameterOrder: continue
                    parameter = function['arguments'][parameterOrder]
                    # if there is a function definition in the same file
                    # use only that
                    if function['filename'] == node.filename:
                        parameters = [parameter]
                        break
                    else:
                        parameters.append(parameter)
                
                for parameter in parameters:
                    node.addDataFlowEdge("passed", parameter)
        
        # handle return from function
        # connect return to function call
        if node.isCallExpression():
            key = node.getIdentifierOfFunctionCall()
            returns = []
            
            if key in self.functionSymbolTable:
                for func in self.functionSymbolTable[key]:
                    # prioritize function return in current file
                    if func['filename'] == node.filename:
                        returns = [func['returns']]
                    else:
                        returns.append(func['returns'])
            
            # flatten array
            returns = [item for sub_list in returns for item in sub_list]
            for returnId in returns:
                node.addDataFlowEdge('returned', returnId)

    def determineScopeNode(self, node: IRNode, prevScope: str) -> str:
        currScope = prevScope
        scopeIdentifiers = PYTHON_DATA_SCOPE_IDENTIFIERS
        controlScopeIdentifiers = PYTHON_CONTROL_SCOPE_IDENTIFIERS
        currentIdentifier = ""

        # add new scope for children if this node is class, function, module, and if-else branch
        if node.type in scopeIdentifiers:
            for child in node.node.children:
                # get the class, function, or module name
                if child.type == "identifier":
                    # store name to pass down to the children
                    currentIdentifier = child.text.decode("utf-8")
        # add new scope for children if this node is child of a control statement
        elif node.type in controlScopeIdentifiers and node.parent is not None and node.parent.isControlStatement():
                if node.controlId != None:
                    currentIdentifier = f"{node.type}{node.controlId}"
                else:
                    currentIdentifier = f"{node.type}{uuid.uuid4().hex}"

        if currentIdentifier != "":
            currScope += f"\{currentIdentifier}"

        return currScope
    
    def connectDataFlowEdgeToOutsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        for targetScope in scopeDatabase:
            if targetScope == node.scope:
                continue

            targetDataScope = self.getDataScope(targetScope)
            currentDataScope = self.getDataScope(node.scope)

            if targetDataScope != currentDataScope:
                continue

            targetKey = (node.content, targetScope)
            # check previous key exists in symbol table
            if targetKey in symbolTable:
                # check no key exists yet in current scope
                if key not in symbolTable:
                    dfgParentId = symbolTable[targetKey][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                elif key in symbolTable and len(symbolTable[key]) <= 1:
                    # handle variable is used for its own assignment
                    '''
                    test = "test"
                    if True:
                        test = test.split("")
                    '''
                    '''
                    test = "test"
                    if True:
                        test = call(test)
                    '''
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = symbolTable[targetKey][-1]
                        node.addDataFlowEdge(dataType, dfgParentId)

    def connectDataFlowEdgeToInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        # iterate through every scope registered
        currentDataScope = self.getDataScope(node.scope)
        for scope in scopeDatabase:
            if scope == None:
                continue

            targetDataScope = self.getDataScope(scope)
            if targetDataScope != currentDataScope:
                continue

            if not self.isControlScope(scope):
                continue
            
            controlKey = (node.content, scope)
            if controlKey in symbolTable:
                insideId = symbolTable[controlKey][-1]
            else:
                continue

            if key in symbolTable:
                outsideId = symbolTable[key][-1]
                outsideOrder = visitedList.index(outsideId)
            else:
                outsideOrder = -1

                insideOrder = visitedList.index(insideId)
                currentOrder = visitedList.index(node.id)

                # make sure last outside occurance of variable is BEFORE if statement
                # and make sure last inside occurance of variable is BEFORE current occurance
                if outsideOrder < insideOrder and insideOrder < currentOrder:
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = symbolTable[controlKey][-2] if len(symbolTable[controlKey]) > 1 else None
                    else:
                        dfgParentId = symbolTable[controlKey][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                    # handle variable in argument list in function
                    if node.isPartOfCallExpression():
                        nodeCall = node.getCallExpression()
                        nodeCall.addDataFlowEdge(dataType, node.id)

    # only for languages that don't have scopes in if else blocks
    # looking at you python
    # connect between two nodes, both of which are inside a control branch
    # where current node is referencing or calling the other node
    # check with outside 
    '''
    a = x
    if ...:
        a = "test"
    if ...:
        print(a)
    '''
    def connectDataFlowEdgeToInsideFromInsideIfElseBranch(self, node: IRNode, key: tuple, dataType: str, visited: set, visitedList: list, scopeDatabase: set, symbolTable: dict):
        currentDataScope = self.getDataScope(node.scope)

        # iterate through every scope registered
        for scope in scopeDatabase:
            if scope == None:
                continue

            targetDataScope = self.getDataScope(node.scope)
            # check data scope is identical
            if targetDataScope != currentDataScope:
                continue

            targetGlobalScope, _, targetControlScope = scope.rpartition("\\")
            currentGlobalScope, _, currentControlScope = node.scope.rpartition("\\")

            # check both scope is inside control branch
            if not self.isControlScope(scope) or not self.isControlScope(node.scope):
                continue
            # check if-else id(s) to make sure scopes aren't from the same branch
            if self.getControlId(targetControlScope) == self.getControlId(currentControlScope):
                continue

            controlKey = (node.content, scope)
            outsideKey = (node.content, targetDataScope)
            if controlKey in symbolTable and outsideKey in symbolTable:
                outsideId = symbolTable[outsideKey][-1]
                insideId = symbolTable[controlKey][-1]
                outsideOrder = visitedList.index(outsideId)
                insideOrder = visitedList.index(insideId)
                currentOrder = visitedList.index(node.id)

                # make sure last outside occurance of variable is BEFORE if statement
                # and make sure last inside occurance of variable is BEFORE current occurance
                if outsideOrder < insideOrder and insideOrder < currentOrder:
                    if node.isPartOfAssignment() and node.getIdentifierFromAssignment() == node.content:
                        dfgParentId = symbolTable[controlKey][-2] if len(symbolTable[controlKey]) > 1 else None
                    else:
                        dfgParentId = symbolTable[controlKey][-1]
                    node.addDataFlowEdge(dataType, dfgParentId)
                    # handle variable in argument list in function
                    if node.isPartOfCallExpression():
                        nodeCall = node.getCallExpression()
                        nodeCall.addDataFlowEdge(dataType, node.id)

    
    def createDataFlowTreeDFS(self, root: Node, filename: str) -> IRNode:
        projectId = uuid.uuid4().hex
        irRoot = IRPythonNode(root, filename, projectId)

        # to keep track of all visited nodes
        visited = set()
        # to keep track of order of visited nodes
        visitedList = []
        # to keep track of variables
        symbolTable = {}
        # to keep track of scopes
        scopeDatabase = set()
        # for dfs
        stack: list[tuple(IRNode, str)] = [(irRoot, filename)]

        while stack:
            payload = stack.pop()
            node: IRNode = payload[0]
            scope: str = payload[1]

            visited.add(node.id)
            visitedList.append(node.id)
            scopeDatabase.add(scope)

            # do the ting
            node.setDataFlowProps(self.sources, self.sinks, self.sanitizers)
            scope = self.determineScopeNode(node, scope)
            self.setNodeDataFlowEdges(node, visited, visitedList, scopeDatabase, symbolTable)
            
            controlId = uuid.uuid4().hex
            
            for child in node.node.children:
                if not self.isIgnoredType(child):
                    if node.type == "if_statement":
                        irChild = IRPythonNode(child, node.filename, node.projectId, controlId=controlId, parent=node)
                    else:
                        irChild = IRPythonNode(child, node.filename, node.projectId, parent=node)
                    node.astChildren.append(irChild)
            stack.extend(reversed([(child, scope) for child in node.astChildren]))
        
        return irRoot
    
    def isControlScope(self, scope: str) -> bool:
        return len(scope.rpartition("\\")[2]) > 32 and scope.rpartition("\\")[2][:-32] in PYTHON_CONTROL_SCOPE_IDENTIFIERS
    
    def getControlId(self, scope: str) -> str:
        return scope[-32:] if self.isControlScope(scope) else ""