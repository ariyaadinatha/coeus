from tree_sitter import Node
import uuid
from typing import Union

test = "huhuhuhu"

# all node from tree-sitter parse result
class ASTNode:
    def __init__(self, node: Node, filename: str, parent=None) -> None:
        if self.isIgnoredType(node):
          self.id = None
          return
        else:
          self.id = uuid.uuid4().hex
          self.controlFlowEdges = None
          self.dataFlowEdges: list[DataFlowEdge] = []

          # get info from tree-sitter node
          self.treeSitterId = node.id
          self.content = node.text.decode("utf-8")
          self.type = node.type
          self.node = node
          self.astChildren: list[ASTNode] = []

          # data flow props
          self.scope = None
          self.isSource = None
          self.isSink = None
          self.isTainted = None

          # control flow props

          # if root
          if type(parent) is ASTNode:
            self.parent = parent
            self.parentId = parent.id
          else:
            self.parent = None
            self.parentId = None
            self.scope = filename
            self.isSource = False
            self.isSink = False
            self.isTainted = False
    
    def __str__(self) -> str:
      return f'[{self.id}] ({self.scope}) {self.type} : {self.content}'

    def isIgnoredType(self, node: Node) -> bool:
      ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']
      
      if node.type in ignoredList:
        return True
      
      return False
    
    def setScope(self, node: Node, parent=None, filename=None):
      # TODO: handle based on language
      # TODO: handle self
      # TODO: handle import
      if parent is None:
          scope = filename
      else:
        # TODO: handle class scope
        # TODO: handle function scope
        # TODO: handle module scope
        scope = self.parent.scope
        if self.parent.parent is not None and self.parent.parent.scope != self.parent.scope:
            scope += f"\${self.parent.scope}"
        
      # self.scope = scope
    
    def createCfgNode(self, statementOrder: int):
      if self.controlFlowEdges is None:
        self.controlFlowEdges = ControlFlowProps(statementOrder)

    def addDataFlowEdge(self, dataType: str, dfgParentId: Union[str, None]):
        edge = DataFlowEdge(dataType, dfgParentId)
        self.dataFlowEdges.append(edge)

# class to store all control flow related actions
class ControlFlowProps:
    def __init__(self, statementOrder: int) -> None:
        self.cfgId = uuid.uuid4().hex
        self.statementOrder = statementOrder

# clas to store all variables and their values
class DataFlowEdge:
    def __init__(self, dataType: str, dfgParentId:  Union[str, None]) -> None:
      # determine whether node is a variable or variable value
      self.dfgId = uuid.uuid4().hex
      self.dfgParentId = dfgParentId
      self.dataType = dataType