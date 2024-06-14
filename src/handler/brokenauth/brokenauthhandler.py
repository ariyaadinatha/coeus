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
        self.insertAllCallEdgesToNeo4j(astRoot)
        self.setLabels()
    
    def buildAstTreeFile(self, fileHandler: FileHandler, codePath: str) -> IRNode:
        source = fileHandler.readFile(codePath)
        code = CodeProcessor(self.language, source)
        root = code.getRootNode()
        astRoot = self.converter.createAstTree(root, codePath)
        self.converter.registerFunctionsToSymbolTable(astRoot)

        return astRoot

    ### Role Control Flow Analysis
    def analysis(self):
        roots = []
        endpoints: list[IRNode] = []
        self.deleteAllNodesAndRelationshipsByAPOC()

        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)

        for codePath in fh.getCodeFilesPath():
            if codePath.split('.')[-1] != EXTENSION_ALIAS[self.language]:
                continue
        
            astRoot = self.buildAstTreeFile(fh, codePath)
            roots.append(astRoot)

        for root in roots:
            rootEndpoints: list[IRNode] = self.converter.identifyEndpoints(root)
            for re in rootEndpoints:
                reCh: list[IRNode] = []
                for ch in re.astChildren:
                    reCh.append(ch)
                re.addControlFlowEdge(reCh[0], reCh[0].id)
                for i in range(len(reCh) - 1):
                    reCh[i].addControlFlowEdge(reCh[i+1], reCh[i+1].id)
                efb = reCh[-1].astChildren[-1]
                reCh[-1].addControlFlowEdge(efb.astChildren[0], efb.astChildren[0].id)
                self.converter.addControlFlowEdgesToTree(efb)
            
            endpoints.extend(rootEndpoints)

            self.converter.addControlFlowEdgesToTree(root)
            self.converter.addCallEdgesToTree()

            self.insertAllNodesToNeo4j(root)
            self.insertAllCFGEdgesToNeo4j(root)
            self.insertAllCallEdgesToNeo4j(root)

        self.createASTRel()
        self.setLabels()

        # for endp in endpoints:
        #     pass

        exp = endpoints[2]
        print(exp.content)

        ### try analyzing an endpoint
        specA = {
            "role": "a",
            "rel": "ROLE_A_PATH_TO"
        }

        specB = {
            "role": "b",
            "rel": "ROLE_B_PATH_TO"
        }

        self.rolePathAnalysis(exp, specA)
        self.rolePathAnalysis(exp, specB)


    def rolePathAnalysis(self, node: IRNode, spec):
        self.nodePathAnalysis(node, spec)
        query = ''''''
        if spec["role"] == "a":
            query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = parent.role_a_path_child_id
                        CREATE (child)<-[r:ROLE_A_PATH_TO]-(parent)
                    '''
        else:
            query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = parent.role_b_path_child_id
                        CREATE (child)<-[r:ROLE_B_PATH_TO]-(parent)
                    '''
        self.Neo4jQuery("", query)

    def nodePathAnalysis(self, node: IRNode, spec):
        # acquire cfg edges
        edgeList = node.controlFlowEdges
        if len(edgeList) == 0:
            return

        edge = edgeList[0]

        if spec["role"] == "a":
            node.roleAPathChildId = edge.cfgChildId
            query = '''
                    MATCH (n)
                    WHERE n.id = $id
                    SET n.role_a_path_child_id = $role_a_path_child_id
                '''
            param = {
                "id": node.id,
                "role_a_path_child_id": node.roleAPathChildId
            }
            self.Neo4jQuery("", query, param)

        elif spec["role"] == "b":
            node.roleBPathChildId = edge.cfgChildId
            query = '''
                    MATCH (n)
                    WHERE n.id = $id
                    SET n.role_b_path_child_id = $role_b_path_child_id
                '''
            param = {
                "id": node.id,
                "role_b_path_child_id": node.roleAPathChildId
            }
            self.Neo4jQuery("", query, param)
        
        self.nodePathAnalysis(edge.cfgChild, spec)

    '''
        Neo4j
    '''
    ### Neo4j query
    def Neo4jQuery(self, command, query, parameters=None):
        try:
            # print(command)
            self.connection.query(query, parameters, db=self.dbName)
        except Exception as e:
            print(f"Query {command} error: {traceback.print_exc()}")
    
    ### Insert AST nodes and edges to Neo4j
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
            endPoint: $endPoint,
            is_endpoint: $is_endpoint,
            is_call: $is_call,
            is_check: $is_check,
            role_a_path_child_id: $role_a_path_child_id,
            role_b_path_child_id: $role_b_path_child_id
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
            "is_endpoint": node.isEndpoint,
            "is_call": node.isCall,
            "is_check": node.isCheck,
            "role_a_path_child_id": node.roleAPathChildId,
            "role_b_path_child_id": node.roleBPathChildId,
        }

        self.Neo4jQuery(command, query, parameters)

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

    def createASTRel(self):
        command = "Inserting edge to Neo4j..."
        query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.parent_id = parent.id
                    CREATE (child)<-[r:AST_PARENT_TO]-(parent)
                '''
        self.Neo4jQuery(command, query)

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
                "cfg_child_id": edge.cfgChildId,
                "control_type": edge.controlType
            }

            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $cfg_child_id AND parent.id = $id
                    CREATE (child)<-[r:CONTROL_FLOW_TO{control_type: $control_type}]-(parent)
                    SET child:ControlNode
                    SET parent:ControlNode
                '''

            try:
                # print("creating control flow relationship")
                self.connection.query(query, parameters=parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create control flow relationship error: {traceback.print_exc()}")

    ### Insert all call edges to Neo4j
    def insertAllCallEdgesToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.controlFlowEdges) != 0:
                self.createCallRel(node)

            for child in node.astChildren:
                queue.append(child)

    def createCallRel(self, node: IRNode):
        for edge in node.callEdges:
            parameters = {
                "id": node.id,
                "call_child_id": edge.callChildId,
                "call_type": edge.callType
            }

            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $call_child_id AND parent.id = $id
                    CREATE (child)<-[r:CALL_TO{call_type: $call_type}]-(parent)
                '''

            try:
                # print("creating control flow relationship")
                self.connection.query(query, parameters=parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create call relationship error: {traceback.print_exc()}")

    ### Set all labels
    def setLabels(self):
        self.setRootLabel()
        self.setEndpointLabel()
        self.setCallLabel()
        self.setCheckLabel()

    def setRootLabel(self):
        command = "Setting root label..."
        query = '''
            MATCH (n) WHERE n.parent_id IS NULL
            SET n:Root
        '''
        self.Neo4jQuery(command, query)

    def setEndpointLabel(self):
        command = "Setting endpoint label..."
        query = '''
            MATCH (n) WHERE n.is_endpoint = true
            SET n:EndpointNode
        '''
        self.Neo4jQuery(command, query)

    def setCallLabel(self):
        command = "Setting call label..."
        query = '''
            MATCH (n) WHERE n.is_call = true
            SET n:CallNode
        '''
        self.Neo4jQuery(command, query)

    def setCheckLabel(self):
        command = "Setting check label..."
        query = '''
            MATCH (n) WHERE n.is_check = true
            SET n:CheckNode
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

    

