from tree_sitter import Node
import uuid

# all node from tree-sitter parse result
class ASTNode:
    def __init__(self, node: Node, parent=None) -> None:
        if self.isIgnoredType(node):
          self.id = None
          return
        else:
          self.id = uuid.uuid4().hex
          self.treeSitterId = node.id
          self.content = node.text.decode("utf-8")
          self.type = node.type
          self.node = node
          self.astChildren = []
          self.controlFlowProps = None
          self.dataFlowProps = None
          
          # check node is root or not
          if type(parent) is ASTNode:
            self.parent = parent
            self.parentId = parent.id
          else:
            self.parent = None
            self.parentId = None
    
    def __str__(self) -> str:
      return f'[{self.id}] {self.type} : {self.content}'

    def isIgnoredType(self, node: Node) -> bool:
      ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

      if node.type in ignoredList:
        return True
      
      return False
    
    def createCfgNode(self, statementOrder: int):
      self.controlFlowProps = ControlFlowProps(statementOrder)

    def createDfgNode(self, dfgParentId, isVariable, type, scope):
      self.dataFlowProps = DataFlowProps(dfgParentId)

# class to store all control flow related actions
class ControlFlowProps:
    def __init__(self, statementOrder: int) -> None:
        self.cfgId = uuid.uuid4().hex
        self.statementOrder = statementOrder

# clas to store all variables and their values
class DataFlowProps:
    def __init__(self, dfgParentId=None) -> None:
      # determine whether node is a variable or variable value
      self.dfgId = uuid.uuid4().hex
      self.dfgParentId = dfgParentId
      # self.scope = 
      # TODO: determine the variable scope
