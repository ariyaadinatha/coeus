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

    def isIgnoredType(self, node: Node) -> bool:
      ignoredList = ['"', '=', '(', ')', '[', ']', ':', '{', '}']

      if node.type in ignoredList:
        return True
      
      return False
    
    def createCfgNode(self, statementOrder: int):
      self.controlFlowProps = ControlFlowProps(statementOrder)

    def createDfgNode(self, dfgParent):
      if self.parent.type == "assignment":
        self.dataFlowProps = DataFlowProps(dfgParent)

# class to store all control flow related actions
class ControlFlowProps:
    def __init__(self, statementOrder: int) -> None:
        self.cfgId = uuid.uuid4().hex
        self.statementOrder = statementOrder

# clas to store all variables and their values
class DataFlowProps:
    def __init__(self, dfgParent=None) -> None:
      # determine whether node is a variable or variable value
      self.dfgId = uuid.uuid4().hex
      # TODO: determine the variable scope
      
      # determine whether a dataflow exists from parent to this node
      if type(dfgParent) is DataFlowProps:
        self.dfgParentId = dfgParent.dfgId
