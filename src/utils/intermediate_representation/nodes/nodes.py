from tree_sitter import Node
import uuid
from utils.constant.intermediate_representation import PYTHON_CONTROL_SCOPE_IDENTIFIERS
from typing import Union
from abc import ABC, abstractmethod

# all node from tree-sitter parse result
class IRNode(ABC):
    def __init__(self, node: Node, filename: str, projectId: str, controlId=None, parent=None) -> None:
        self.id = uuid.uuid4().hex
        self.controlFlowEdges: list[ControlFlowEdge] = []
        self.dataFlowEdges: list[DataFlowEdge] = []

        # get info from tree-sitter node
        self.treeSitterId = node.id
        self.content = node.text.decode("utf-8")
        self.type = node.type
        self.node = node
        self.startPoint = node.start_point
        self.endPoint = node.end_point
        self.astChildren: list[IRNode] = []

        # metadata info
        self.filename = filename
        self.projectId = projectId

        # data flow props
        self.scope = None
        self.isSource = False
        self.isSink = False
        self.isTainted = False
        self.isSanitizer = False

        if controlId != None:
            self.controlId = controlId
        else:
            self.controlId = None

        # control flow props

        # if root
        if isinstance(parent, IRNode):
            self.parent = parent
            self.parentId = parent.id
        else:
            self.parent = None
            self.parentId = None
            self.scope = filename
            self.isSource = False
            self.isSink = False
            self.isTainted = False
    
    # print shortcut
    def __str__(self) -> str:
        return f'[{self.id}] {self.type} : {self.content}'
    
    def printChildren(self, depth=0):
        indent = ' ' * depth

        print(f'{indent}{self}')
        # print(f'{indent}{self.scope}')
        # control flow info
        # for control in node.controlFlowEdges:
        #     print(f'{indent}[control] {control.cfgParentId} - {control.statementOrder}')

        # taint analysis info
        #   print(f'{indent}sink {self.isSink}')
        #   print(f'{indent}source {self.isSource}')
        #   print(f'{indent}sanitizer {self.isSanitizer}')

        # data flow info
        #   for data in self.dataFlowEdges:
        #       print(f'{indent}[data] {data.dfgParentId} - {data.dataType}')
        
        for child in self.astChildren:
            child.printChildren(depth + 2)

    def isIgnoredType(self, node: Node) -> bool:
        ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']
        
        if node.type in ignoredList:
            return True
        
        return False
    
    def setDataFlowProps(self, sources, sinks, sanitizers):
        self.isSource = self.checkIsSource(sources)
        self.isSink = self.checkIsSink(sinks)
        self.isSanitizer = self.checkIsSanitizer(sanitizers)
        self.isTainted = self.isSource
    
    def addControlFlowEdge(self, statementOrder: int, cfgParentId: Union[str, None], controlType: str='next_statement'):
        edge = ControlFlowEdge(statementOrder, cfgParentId, controlType)
        self.controlFlowEdges.append(edge)

    def addDataFlowEdge(self, dataType: str, dfgParentId: Union[str, None], parameterOrder: int = 0):
        edge = DataFlowEdge(dataType, dfgParentId, parameterOrder)
        if edge not in self.dataFlowEdges and dfgParentId != self.id:
            self.dataFlowEdges.append(edge)

    def checkIsSource(self, sources) -> bool:
        if self.parent == None: return False
        # handle declaration of source in function
        # ex: public AttackResult attack(@RequestParam String userId)
        if (self.isIdentifier() and self.isArgumentOfAFunctionDefinition() and "@RequestParam" in self.parent.content):
            return True
        for source in sources:
            if source.lower() in self.content.lower():
                return True
        return False
    
    def checkIsSink(self, sinks) -> bool:
        if self.parent == None: return False
        for sink in sinks:
            if sink.lower() in self.content.lower() and (self.isCallExpression() or self.isPartOfCallExpression()):
                return True
        return False
    
    def checkIsSanitizer(self, sanitizers) -> bool:
        if self.parent == None: return False
        for sanitizer in sanitizers:
            if sanitizer.lower() in self.content.lower():
                return True
        return False
    
    def isInLeftHandSide(self) -> bool:
        if self.node.prev_sibling is not None:
            return False
        
        siblings = self.node.parent.children

        i = 0
        while len(siblings) != 0:
            # if loop find self node first, is in left hand side
            # if loop find equal operator first, is in right hand side
            if siblings[i].text.decode("utf-8") == self.content:
                return True
            if siblings[i].text.decode("utf-8") == "=":
                return False
            
        return False

    def isAssignmentStatement(self) -> bool:
        return "assignment" in self.type or "declarator" in self.type or "declaration" in self.type
    
    def isDirectlyInvolvedInAssignment(self) -> bool:
        return self.parent.isAssignmentStatement()
        
    def isPartOfPatternAssignment(self) -> bool:
        if self.isAssignmentStatement():
            return False
        
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isAssignmentStatement():
                if "pattern" in parent.node.children[0].type or "list_literal" in parent.node.children[0].type:
                    return True
                return False
            else:
                parent = parent.parent

        return False
    
    def isInRightHandSide(self) -> bool:
        return self.node.prev_sibling is not None and self.node.prev_sibling.type != "$"
    
    def isValueOfAssignment(self) -> bool:
        # a = x
        if self.isInRightHandSide() and self.isDirectlyInvolvedInAssignment():
            return True
        # a = "test" + x
        elif self.isPartOfAssignment():
            assignmentChildNode = self.parent

            while assignmentChildNode is not None and not assignmentChildNode.isControlStatement():
                if assignmentChildNode.parent is None:
                    return False
                
                if assignmentChildNode.parent.isAssignmentStatement():
                    childNode = assignmentChildNode.node
                    while childNode is not None and childNode.type != "=":
                        childNode = childNode.prev_sibling
                    return childNode is not None and childNode.type == "="
                else:
                    assignmentChildNode = assignmentChildNode.parent
            return False
        return False
    
    def isIdentifier(self) -> bool:
        return ("identifier" in self.type or self.type == "variable_name") and self.type != "type_identifier"
    
    def isAttribute(self) -> bool:
        return "attribute" in self.type or "member_expression" in self.type or "member_access_expression" in self.type or "field_access" in self.type
    
    def isFunctionDefinition(self) -> bool:
        return self.type == "function_definition" or self.type == "method_definition" or self.type == "function_declaration" or self.type == "method_declaration" or self.type == "arrow_function"
    
    def isImportStatement(self) -> bool:
        return "import_from_statement" in self.type or "import_statement" in self.type

    def isReturnStatement(self) -> bool:
        return self.type == "return_statement"
    
    def isPartOfReturnStatement(self) -> bool:
        if not self.isIdentifier():
            return False
        
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isReturnStatement():
                return True
            parent = parent.parent

        return False

    def getCallExpression(self):
        parent = self.parent

        while parent is not None and not parent.isCallExpression():
            parent = parent.parent

        return parent
    
    def getFunctionDefinition(self):
        parent = self.parent

        while parent is not None and not parent.isFunctionDefinition():
            parent = parent.parent

        return parent
    
    def getIdentifierFromFunctionDefinition(self) -> str:
        definition = self.getFunctionDefinition()

        if definition is None:
            return None

        for attr in definition.astChildren:
            if attr.isIdentifier() or attr.type == "name":
                return attr.content
            
    def getIdentifierOfFunctionCall(self) -> str:
        if "echo" in self.type:
            return None
        
        first = self.astChildren[0]
        if first.isIdentifier() or first.type == "name":
            return first.content
        else:
            # handle method call from class
            # ex: Example.sink(test) -> Example is the first identifier then sink
            # to always get the identifier, we get the last child
            identifiers = [attr.content for attr in first.astChildren if attr.isIdentifier()]
            if len(identifiers) < 1:
                return None
            else:
                return identifiers[-1]
    
    def getFunctionAttributesFromFunctionCall(self) -> list:
        call = self.getCallExpression()

        if call == None:
            print(self)
            return []

        first = call.astChildren[0]
        if (first.isIdentifier() or first.type == "name") and first.node.next_sibling.type != ".":
            return [first.content]
        else:
            # handle method call from class
            # ex: Example.sink(test) -> Example is the first identifier then sink
            # to always get the identifier, we get the last child
            identifiers = [attr.content for attr in first.astChildren if attr.isIdentifier()]
            if len(identifiers) < 1:
                return []
            else:
                return identifiers
    
    def getBinaryExpression(self):
        parent = self.parent

        while not parent.isBinaryExpression():
            parent = parent.parent

        return parent
    
    def isPartOfCallExpression(self) -> bool:
        parent = self.parent
        while parent is not None and not parent.isControlStatement() and not parent.isAssignmentStatement():
            if parent.isCallExpression():
                return True
            parent = parent.parent

        return False
    
    def isPartOfBinaryExpression(self) -> bool:
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isBinaryExpression():
                return True
            parent = parent.parent

        return False
    
    def isPartOfAssignment(self) -> bool:
        if self.isAssignmentStatement():
            return False
        
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isAssignmentStatement():
                return True
            else:
                parent = parent.parent

        return False
    
    def getIdentifiersFromPatternAssignment(self) -> str:
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if parent.isAssignmentStatement():
                if "pattern" in parent.node.children[0].type or "list_literal" in parent.node.children[0].type:
                    patternNode = parent.node.children[0]
                    return [identifier.text.decode("utf-8") for identifier in patternNode.children]
                return None
            else:
                parent = parent.parent

        return None
    
    def getOrderOfParametersInFunction(self) -> int:
        if not (self.isArgumentOfAFunctionDefinition() or self.isArgumentOfAFunctionCall()):
            return 0
        
        parameters = self.parent.astChildren
        for index, node in enumerate(parameters):
            if node.id == self.id:
                return index
        
        return 0

    def getImportOriginAndName(self):
        pass
        # if not self.isImportStatement():
        #     return None
        
        # origin = []
        # for child in self.astChildren:
        #     for identifier in child.astChildren:
        #         if identifier.isIdentifier():
        #             origin.append(identifier.content)

        # return origin[-1], origin

    @abstractmethod
    def isBinaryExpression(self) -> bool:
        pass
    
    @abstractmethod
    def isCallExpression(self) -> bool:
        pass

    @abstractmethod
    def isControlStatement(self) -> bool:
        pass
    
    @abstractmethod
    def isIdentifierOfFunctionDefinition(self) -> bool:
        pass

    # argument of function definition
    @abstractmethod
    def isArgumentOfAFunctionDefinition(self) -> str:
        pass

    # argument of function call
    @abstractmethod
    def isArgumentOfAFunctionCall(self) -> str:
        pass

    # node is function definition
    @abstractmethod
    def getParameters(self) -> list:
        pass

    @abstractmethod
    def isDivergingControlStatement(self) -> bool:
        pass
    
    @abstractmethod
    def getIdentifierFromAssignment(self) -> str:
        pass

# class to store all control flow related actions
class ControlFlowEdge:
    def __init__(self, statementOrder: int, cfgParentId: str, controlType: str = 'next_statement') -> None:
        self.cfgId = uuid.uuid4().hex
        self.statementOrder = statementOrder
        self.cfgParentId = cfgParentId
        self.controlType = controlType

# clas to store all variables and their values
class DataFlowEdge:
    def __init__(self, dataType: str, dfgParentId:  Union[str, None], parameterOrder: int = 0) -> None:
        # determine whether node is a variable or variable value
        self.dfgId = uuid.uuid4().hex
        self.dfgParentId = dfgParentId
        self.dataType = dataType
        self.parameterOrder = parameterOrder