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
      # control flow info
      # for control in node.controlFlowEdges:
      #     print(f'{indent}[control] {control.cfgParentId} - {control.statementOrder}')

      # taint analysis info
      print(f'{indent}sink {self.isSink}')
      print(f'{indent}source {self.isSource}')
      print(f'{indent}sanitizer {self.isSanitizer}')

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
    
    def setDataFlowProps(self, scope, sources, sinks, sanitizers):
      self.isSource = self.checkIsSource(sources)
      self.isSink = self.checkIsSink(sinks)
      self.isSanitizer = self.checkIsSanitizer(sanitizers)
      self.isTainted = self.isSource
      self.scope = scope
    
    def addControlFlowEdge(self, statementOrder: int, cfgParentId: Union[str, None], controlType: str='next_statement'):
      edge = ControlFlowEdge(statementOrder, cfgParentId, controlType)
      self.controlFlowEdges.append(edge)

    def addDataFlowEdge(self, dataType: str, dfgParentId: Union[str, None]):
        edge = DataFlowEdge(dataType, dfgParentId)
        if edge not in self.dataFlowEdges and dfgParentId != self.id:
            self.dataFlowEdges.append(edge)

    def checkIsSource(self, sources) -> bool:
        if self.parent == None: return False
        for source in sources:
            if source.lower() in self.content.lower():
                return True
        return False
    
    def checkIsSink(self, sinks) -> bool:
        if self.parent == None: return False
        if not self.isCallExpression(): return False
        for sink in sinks:
            if sink.lower() in self.content.lower():
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
        return "identifier" in self.type or self.type == "variable_name"
    
    def isAttribute(self) -> bool:
        return "attribute" in self.type or "member_expression" in self.type or "member_access_expression" in self.type or "field_access" in self.type
    
    def getCallExpression(self):
        parent = self.parent

        while not parent.isCallExpression():
            parent = parent.parent

        return parent
    
    def getBinaryExpression(self):
        parent = self.parent

        while not parent.isBinaryExpression():
            parent = parent.parent

        return parent
    
    def isPartOfCallExpression(self) -> bool:
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
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
    
    @abstractmethod
    def isBinaryExpression(self) -> bool:
        pass
    
    @abstractmethod
    def isCallExpression(self) -> bool:
        pass

    @abstractmethod
    def isControlStatement(self) -> bool:
        pass

    # to handle source declared in parameter in Java
    # ex: @RequestParam userId
    @abstractmethod
    def isArgumentOfAFunction(self) -> str:
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
    def __init__(self, dataType: str, dfgParentId:  Union[str, None]) -> None:
      # determine whether node is a variable or variable value
      self.dfgId = uuid.uuid4().hex
      self.dfgParentId = dfgParentId
      self.dataType = dataType