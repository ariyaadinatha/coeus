from utils.neo4j import Neo4jConnection
from utils.intermediate_representation.converter.converter import IRConverter
from utils.intermediate_representation.converter.irpythonconverter import IRPythonConverter
from utils.intermediate_representation.converter.irjavascriptconverter import IRJavascriptConverter
from utils.intermediate_representation.converter.irjavaconverter import IRJavaConverter
from utils.intermediate_representation.converter.irphpconverter import IRPhpConverter
from utils.intermediate_representation.nodes.nodes import IRNode, DataFlowEdge, ControlFlowEdge
from utils.codehandler import FileHandler, CodeProcessor
from utils.vulnhandler import VulnerableHandler, Vulnerable
from utils.constant.code import EXTENSION_ALIAS
from datetime import datetime
from neo4j.graph import Path
import time
import os
import json
import traceback
import re

class ACHandler:
    '''
        Initialization
    '''
    def __init__(self, projectPath: str, language: str):
        # initialize connection to Neo4j
        self.dbName = os.getenv('DB_NAME')
        try:
            self.connection = Neo4jConnection(os.getenv('DB_URI'), os.getenv('DB_USER'), os.getenv('DB_PASS'))
        except Exception as e:
            print("Failed to create the driver:", e)
        

        # set project path & language
        self.projectPath = projectPath
        self.language = language

        # create converter to AST
        self.converter = self.createConverter()

        # TODO
    
    '''
        Utils
    '''
    ### Create IR converter
    def createConverter(self) -> IRConverter:
        if self.language == "python":
            return IRPythonConverter()
        elif self.language == "javascript":
            return IRJavascriptConverter()
        elif self.language == "php":
            return IRPhpConverter()
        elif self.language == "java":
            return IRJavaConverter()

    ### Build complete repository AST
    def buildTreeRepository(self):
        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)

        for codePath in fh.getCodeFilesPath():
            if codePath.split('.')[-1] != EXTENSION_ALIAS[self.language]:
                continue
            self.buildTreeFile(fh, codePath)

    ### build AST from a single file
    def buildTreeFile(self, fileHandler: FileHandler, codePath: str):
        source = fileHandler.readFile(codePath)
        code = CodeProcessor(self.language, source)
        root = code.getRootNode()
        astRoot = self.converter.createCompleteTree(root, codePath)
        self.insertAllNodesToNeo4j(astRoot)
        self.insertAllEdgesToNeo4j(astRoot)
        self.insertAllCFGEdgesToNeo4j(astRoot)
        self.insertAllRTEdgesToNeo4j(astRoot)
        self.setLabels()
    '''
        Neo4j
    '''
    ### Neo4j query
    def Neo4jQuery(self, command, query, parameters=None):
        try:
            print(command)
            self.connection.query(query, parameters, db=self.dbName)
            # if parameters != None:
            #     self.connection.query(query, parameters, db=self.dbName)
            # else:
            #     self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query {command} error: {traceback.print_exc()}")
    
    ### Insert all nodes to Neo4j
    def insertAllNodesToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            self.insertNodeToNeo4j(node)

            for child in node.astChildren:
                queue.append(child)

    def insertNodeToNeo4j(self, node: IRNode):
        command = "Inserting node to Neo4j..."
        query = '''CREATE (:Node {
            id: $id, 
            type: $type, 
            content: $content, 
            parent_id: $parent_id, 
            scope: $scope, 
            filename: $filename, 
            startPoint: $startPoint, 
            endPoint: $endPoint
            })'''
        parameters = {
            "id": node.id,
            "type": node.type,
            "content": node.content,
            "parent_id": node.parentId, 
            "scope": node.scope, 
            "filename": node.filename, 
            "startPoint": node.startPoint,
            "endPoint": node.endPoint,
        }

        self.Neo4jQuery(command, query, parameters)

    ### Insert all edges to Neo4j
    def insertAllEdgesToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]
        while len(queue) != 0:
            node = queue.pop(0)
            if len(node.astChildren) != 0:
                self.insertEdgeToNeo4j(node)
            for child in node.astChildren:
                queue.append(child)

    def insertEdgeToNeo4j(self, node: IRNode):
        command = "Inserting edge to Neo4j..."
        query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $id AND parent.id = $parent_id
                    CREATE (child)<-[r:FLOW_TO]-(parent)
                '''
        for child in node.astChildren:
            parameters = {
                "id": child.id,
                "parent_id": node.id
            }
            self.Neo4jQuery(command, query, parameters)

    def identifyAppNode(self, root: IRNode):
        
        queue : list[IRNode] = [root]
        
        while len(queue) != 0:
            
            node = queue.pop(0)
            
            found = False
            
            if node.type == "expression_statement" and node.astChildren[0].type == "assignment":
                child = node.astChildren[0]
                pattern = r"Flask\((.*?)\)"
                for expr in child.astChildren:
                    match = re.match(pattern, expr.content)
                    if bool(match):
                        found = True
                        break
            if found:
                param = {
                    "id":node.id
                }
                query = '''
                    MATCH (n) WHERE n.id=$id
                    SET n:StartApp
                '''
                self.Neo4jQuery(param, query, "setting flask starting point")
                break

            for ch in node.astChildren:
                queue.append(ch)

    ### Insert all CFG edges to Neo4j
    def insertAllCFGEdgesToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.controlFlowEdges) != 0:
                self.createCFGRel(node)

            for child in node.astChildren:
                queue.append(child)
    
    def createCFGRel(self, node: IRNode):
        for edge in node.controlFlowEdges:
            parameters = {
                "id": node.id,
                "cfg_parent_id": edge.cfgParentId,
                "statement_order": edge.statementOrder,
                "control_type": edge.controlType
            }

            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $id AND parent.id = $cfg_parent_id
                    CREATE (child)<-[r:CONTROL_FLOW_TO{statement_order: $statement_order, control_type: $control_type}]-(parent)
                    SET child:ControlNode
                    SET parent:ControlNode
                '''

            try:
                print("creating control flow relationship")
                self.connection.query(query, parameters=parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create control flow relationship error: {traceback.print_exc()}")

    ### Insert all routing edges to Neo4j
    def insertAllRTEdgesToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.routingEdges) != 0:
                self.createRTRel(node)

            for child in node.astChildren:
                queue.append(child)

    def createRTRel(self, node: IRNode):
        for edge in node.routingEdges:
            parameters = {
                "id": node.id,
                "stmt_order": edge.stmtOrder,
                "parent_id": edge.routeParentId,
            }

            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $id AND parent.id = $parent_id
                    CREATE (child)<-[r:ROUTING_TO{stmt_order: $stmt_order}]-(parent)
                    SET child:RouteNode
                    SET parent:RouteNode
                '''

            try:
                print("creating routing relationship")
                self.connection.query(query, parameters=parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create routing relationship error: {traceback.print_exc()}")

    ### Set all labels
    def setLabels(self):
        self.setRootLabel()

    def setRootLabel(self):
        command = "Setting root label..."
        query = '''
            MATCH (n) WHERE n.parent_id IS NULL
            SET n:Root
        '''
        self.Neo4jQuery(command, query)

    ### Reset the database
    def deleteAllNodesAndRelationshipsByAPOC(self):
        query = '''
            CALL apoc.periodic.iterate('MATCH (n) RETURN n', 'DETACH DELETE n', {batchSize:1000})
        '''
        try:
            print("Resetting the database...")
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query delete all nodes and relationships error: {traceback.print_exc()}")

    

