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
        return self.node.prev_sibling is None
    
    def isInRightHandSide(self) -> bool:
        return self.node.prev_sibling is not None and self.node.prev_sibling.type != "$"
    
    def isValueOfAssignment(self) -> bool:
        # a = x
        if self.isInRightHandSide() and self.node.prev_sibling.type == "=" and (self.node.prev_sibling.prev_sibling.type == "identifier" or self.node.prev_sibling.prev_sibling.type == "variable_name"):
            return True
        # a = "test" + x
        if self.isPartOfAssignment() and self.isInRightHandSide():
            return True
        return False
    
    def isIdentifier(self) -> bool:
        return self.type == "identifier" or self.type == "variable_name"
    
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
        if "statement" in self.type:
            return False
        
        parent = self.parent
        while parent is not None and not parent.isControlStatement():
            if "assignment" in parent.type or "declarator" in parent.type:
                return True
            else:
                parent = parent.parent

        return False
    
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