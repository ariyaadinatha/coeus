from tree_sitter import Node
import uuid
from typing import Union

# all node from tree-sitter parse result
class IRNode:
    def __init__(self, node: Node, filename: str, projectId: str, parent=None) -> None:
        if self.isIgnoredType(node):
          self.id = None
          return
        else:
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

          # control flow props

          # if root
          if type(parent) is IRNode:
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
      for data in self.dataFlowEdges:
          print(f'{indent}[data] {data.dfgParentId} - {data.dataType}')

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
      self.scope = scope
    
    def addControlFlowEdge(self, statementOrder: int, cfgParentId: Union[str, None]):
      edge = ControlFlowEdge(statementOrder, cfgParentId)
      self.controlFlowEdges.append(edge)

    def addDataFlowEdge(self, dataType: str, dfgParentId: Union[str, None]):
        edge = DataFlowEdge(dataType, dfgParentId)
        self.dataFlowEdges.append(edge)

    def checkIsSource(self, sources) -> bool:
        for source in sources:
            if source in self.content.lower():
                return True
        return False
    
    def checkIsSink(self, sinks) -> bool:
        for sink in sinks:
            if sink in self.content.lower():
                return True
        return False
    
    def checkIsSanitizer(self, sanitizers) -> bool:
        for sanitizer in sanitizers:
            if sanitizer in self.content.lower():
                return True
        return False

# class to store all control flow related actions
class ControlFlowEdge:
    def __init__(self, statementOrder: int, cfgParentId: str) -> None:
        self.cfgId = uuid.uuid4().hex
        self.statementOrder = statementOrder
        self.cfgParentId = cfgParentId

# clas to store all variables and their values
class DataFlowEdge:
    def __init__(self, dataType: str, dfgParentId:  Union[str, None]) -> None:
      # determine whether node is a variable or variable value
      self.dfgId = uuid.uuid4().hex
      self.dfgParentId = dfgParentId
      self.dataType = dataType