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
from typing import Union
import time
import os
import json
import traceback
import re

class ACHandler:
    '''
        Initialization
    '''
    def __init__(self, projectPath: str, language: str, specPath: str):
        # initialize connection to Neo4j
        self.dbName = os.getenv('DB_NAME')
        try:
            self.connection = Neo4jConnection(os.getenv('DB_URI'), os.getenv('DB_USER'), os.getenv('DB_PASS'))
        except Exception as e:
            print("Failed to create the driver:", e)
        

        # set project path & language
        self.projectPath = projectPath
        self.language = language
        self.specPath = specPath

        # create converter to AST
        self.loadKeywords()
        self.converter = self.createConverter()

        # TODO
    
    '''
        Utils
    '''
    ### Load keywords
    def loadKeywords(self):
        with open(f"./rules/brokenauth/{self.language}-wordlist.json", 'r') as file:
            self.stopWords = json.load(file)["stop_wordlist"]

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

    ### Build complete repository representation
    def buildTreeRepository(self):
        f = open(self.specPath)
        spec = json.load(f)

        # 1. Intermediate representation generation
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
            self.converter.identifyStops(root, self.stopWords)
            self.converter.identifyMiddleware(root, spec["builtins"])
            self.converter.identifyFunctions(root)
            
            rootEndpoints: list[IRNode] = self.converter.identifyEndpoints(root)
            
            endpoints.extend(rootEndpoints)

            self.converter.addControlFlowEdgesToTree(root)
            
            self.insertAllNodesToNeo4j(root)
            self.insertAllCFGEdgesToNeo4j(root)

        self.converter.addCallEdgesToTree()
        
        for root in roots:
            self.insertAllCallEdgesToNeo4j(root)

        self.createASTRel()
        self.setLabels()

    ### build complete representation from a single file
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
    
    ### build AST from a single file
    def buildAstTreeFile(self, fileHandler: FileHandler, codePath: str) -> IRNode:
        source = fileHandler.readFile(codePath)
        code = CodeProcessor(self.language, source)
        root = code.getRootNode()
        astRoot = self.converter.createAstTree(root, codePath)
        self.converter.identifyFunctions(astRoot)
        # self.converter.registerFunctionsToSymbolTable(astRoot)

        return astRoot

    ### Role Path Analysis
    def analysis(self):

        f = open(self.specPath)
        spec = json.load(f)

        # 1. Intermediate representation generation
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
            self.converter.identifyStops(root, self.stopWords)
            self.converter.identifyMiddleware(root, spec["builtins"])
            self.converter.identifyFunctions(root)
            
            rootEndpoints: list[IRNode] = self.converter.identifyEndpoints(root)
            
            endpoints.extend(rootEndpoints)

            self.converter.addControlFlowEdgesToTree(root)
            
            self.insertAllNodesToNeo4j(root)
            self.insertAllCFGEdgesToNeo4j(root)

        self.converter.addCallEdgesToTree()
        
        for root in roots:
            self.insertAllCallEdgesToNeo4j(root)

        self.createASTRel()
        self.setLabels()

        # 2. Vulnerability detection

        ## Read specification input
        endpSpec = spec["endpoints"]
        dataSpec = spec["specification"]
        globalSpec = dataSpec["global"]
        roleASpec = dataSpec["role"]['a']
        roleBSpec = dataSpec["role"]['b']

        roleASpec["data"].update(globalSpec["data"])
        roleASpec["statement"].extend(globalSpec['statement'])
        roleBSpec["data"].update(globalSpec["data"])
        roleBSpec["statement"].extend(globalSpec['statement'])

        dataVarList: set = {i for i in roleASpec['data']}
        roleBVarlist: set = {i for i in roleBSpec['data']}
        dataVarList.update(roleBVarlist)

        ## Endpoint path analysis
        ### If no specified endpoints to analyze
        for endp in endpoints:
            m = re.search(r"[\'\"](.*?)[\'\"]", endp.content)
            route = m.group(1)
            # print(route)
            if len(endpSpec) == 0:
                self.nodePathAnalysis(endp, roleASpec, route, dataVarList)
                self.nodePathAnalysis(endp, roleBSpec, route, dataVarList)
            else:
                if route in endpSpec:
                    self.nodePathAnalysis(endp, roleASpec, route, dataVarList)
                    print()
                    self.nodePathAnalysis(endp, roleBSpec, route, dataVarList)

    def nodePathAnalysis(self, node: IRNode, spec, route: str, dataVarList: set):
        stack: list[IRNode] = [node]
        while stack:

            payload = stack.pop()

            callEdge, cfgEdge = self.getEdges(payload, spec, dataVarList)
            if cfgEdge != None:
                stack.append(cfgEdge.cfgChild)
            if callEdge != None:
                stack.append(callEdge.callChild)

            if payload.isStop:
                break

            if stack:
                self.addPathEdge(payload, stack[-1], spec['role'], route)
                
    def getEdges(self, node: IRNode, spec, dataVarList: set):
        callEdge = None
        cfgEdge = None
        callList = node.callEdges
        cfgList = node.controlFlowEdges

        # acquire call edge
        if len(callList) != 0:
            callEdge = callList[0]
        
        # acquire cfg edge
        ## normal edge (assume)
        if len(cfgList) != 0:
            cfgEdge = cfgList[0]
        
        ## branch
        if node.isCheck:
            ### simple comparisons
            cfgTrueEdge = None
            cfgFalseEdge = None
            for edge in cfgList:
                if edge.controlType == "next_statement_if_true":
                    cfgTrueEdge = edge
                else:
                    cfgFalseEdge = edge
            if (node.type == "comparison_operator" or node.type == "identifier" or node.type == "call"):
                #### if data is specified
                if node.comparison.variable in spec["data"]:
                    if node.comparison.compare(spec['data'][node.comparison.variable]):
                        cfgEdge = cfgTrueEdge
                    else:
                        cfgEdge = cfgFalseEdge
                #### if data is not specified
                else:
                    if node.comparison.variable in dataVarList:
                        cfgEdge = cfgFalseEdge
                    ##### default behavior
                    else:
                        cfgEdge = cfgTrueEdge
            ### complex comparisons
            else:
                stmts = spec['statement']
                if len(stmts) > 0:
                    for stmt in stmts:
                        if node.content == stmt[0]:
                            if stmt[1]:
                                cfgEdge = cfgTrueEdge
                            else:
                                cfgEdge = cfgFalseEdge
                            break 
                else:
                    cfgEdge = cfgFalseEdge

        ## middleware
        if node.isMiddleware:
            ### if middleware is builtin
            if node.isBuiltin:
                if node.builtin.isAllowed(spec):
                    cfgEdge = cfgList[0]
                else:
                    cfgEdge = None 
            ### else, handle like call

        return callEdge, cfgEdge

    def addPathEdge(self, curr: IRNode, next: IRNode, role: str, endpoint: str):
        parameters = {
            "id": curr.id,
            "endpoint": endpoint
        }
        query = ''
        
        if role == 'a':
            curr.roleAPathChildId = next.id
            parameters['role_a_path_child_id'] = curr.roleAPathChildId
            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $role_a_path_child_id AND parent.id = $id
                    SET parent.role_a_path_child_id = $role_a_path_child_id
                    CREATE (child)<-[r:ROLE_A_PATH_TO{endpoint: $endpoint}]-(parent)
                '''
        if role == 'b':
            curr.roleBPathChildId = next.id
            parameters['role_b_path_child_id'] = curr.roleBPathChildId
            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $role_b_path_child_id AND parent.id = $id
                    SET parent.role_b_path_child_id = $role_b_path_child_id
                    CREATE (child)<-[r:ROLE_B_PATH_TO{endpoint: $endpoint}]-(parent)
                '''
        self.Neo4jQuery('', query, parameters)

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
            is_stop: $is_stop,
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
            "is_stop": node.isStop,
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

            if len(node.callEdges) != 0:
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
                self.connection.query(query, parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create call relationship error: {traceback.print_exc()}")

    ### Insert all path edges to Neo4j
    def insertAllPathEdgesToNeo4j(self, root: IRNode, endpoint: str):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.roleAPathChildId) != 0:
                self.createPathRel(node, "a", endpoint)
            
            if len(node.roleBPathChildId) != 0:
                self.createPathRel(node, "b", endpoint)

            for child in node.astChildren:
                queue.append(child)

    def createPathRel(self, node: IRNode, role: str, endpoint: str):
        # if node.type == 'function_definition' and 'login_required' in node.content:
        #     print('flag')
        
        parameters = {
                "id": node.id,
                "endpoint": endpoint
        }

        query = ''

        if role == 'a':
            parameters['role_a_path_child_id'] = node.roleAPathChildId
            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $role_a_path_child_id AND parent.id = $id
                    SET parent.role_a_path_child_id = $role_a_path_child_id
                    CREATE (child)<-[r:ROLE_A_PATH_TO{endpoint: $endpoint}]-(parent)
                '''
        elif role == 'b':
            parameters['role_b_path_child_id'] = node.roleBPathChildId
            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $role_b_path_child_id AND parent.id = $id
                    SET parent.role_b_path_child_id = $role_b_path_child_id
                    CREATE (child)<-[r:ROLE_B_PATH_TO{endpoint: $endpoint}]-(parent)
                '''
        
        self.Neo4jQuery("", query, parameters)

    ### Set all labels
    def setLabels(self):
        self.setRootLabel()
        self.setEndpointLabel()
        self.setCallLabel()
        self.setCheckLabel()
        self.setStopLabel()

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
    
    def setStopLabel(self):
        query = '''
            MATCH (n) WHERE n.is_stop = true
            SET n:StopNode
        '''
        self.Neo4jQuery("", query)

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

    

