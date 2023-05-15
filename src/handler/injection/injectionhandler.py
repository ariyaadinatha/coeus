from utils.neo4j import Neo4jConnection
from utils.intermediate_representation.converter import IRConverter
from utils.intermediate_representation.nodes import IRNode, DataFlowEdge, ControlFlowEdge
from utils.codehandler import FileHandler, CodeProcessor
from utils.vulnhandler import VulnerableHandler, Vulnerable
from datetime import datetime
import time
import os
import json

class InjectionHandler:
    def __init__(self, projectPath: str, language: str):
        try:
            self.connection = Neo4jConnection(os.getenv('DB_URI'), os.getenv('DB_USER'), os.getenv('DB_PASS'))
        except Exception as e:
            print("Failed to create the driver:", e)
        
        self.vulnHandler = VulnerableHandler()
        self.projectPath = projectPath
        self.language = language
        self.loadSourceSinkAndSanitizer()
        self.converter = IRConverter(self.sources, self.sinks, self.sanitizers)

    def loadSourceSinkAndSanitizer(self):
        with open(f"./rules/injection/source-{self.language}-wordlist.json", 'r') as file:
            self.sources = json.load(file)["wordlist"]
        with open(f"./rules/injection/sink-{self.language}-wordlist.json", 'r') as file:
            self.sinks = json.load(file)["wordlist"]
        with open(f"./rules/injection/sanitizer-{self.language}-wordlist.json", 'r') as file:
            self.sanitizers = json.load(file)["wordlist"]

    def buildDataFlowTree(self):
        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)

        extensionAlias = {
        "python": "py",
        "java": "java",
        "javascript": "js",
        "php": "php",
        }
        
        for codePath in fh.getCodeFilesPath():
            if codePath.split('.')[-1] != extensionAlias[self.language]:
                continue
            sourceCode = fh.readFile(codePath)
            code = CodeProcessor(self.language, sourceCode)
            root = code.getRootNode()
            astRoot = self.converter.createDataFlowTree(root, codePath)
            self.insertTreeToNeo4j(astRoot)
            self.insertDataFlowRelationshipsToNeo4j()

    def buildCompleteTree(self):
        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)

        extensionAlias = {
        "python": "py",
        "java": "java",
        "javascript": "js",
        "php": "php",
        }
        
        for codePath in fh.getCodeFilesPath():
            if codePath.split('.')[-1] != extensionAlias[self.language]:
                continue
            sourceCode = fh.readFile(codePath)
            code = CodeProcessor(self.language, sourceCode)
            root = code.getRootNode()
            astRoot = self.converter.createCompleteTree(root, codePath)
            self.insertCompleteTreeToNeo4j(astRoot)
            self.insertAllRelationshipsToNeo4j(astRoot)

            astRoot.printChildren()

    def taintAnalysis(self):
        try:
            self.deleteAllNodesAndRelationshipsByAPOC()
            self.buildDataFlowTree()
            self.propagateTaint()
            self.appySanitizers()
            result = self.getSourceAndSinkInjectionVulnerability()

            return result
        except Exception as e:
            print(e)
            self.deleteAllNodesAndRelationshipsByAPOC()
            raise

    def compareDataFlowAlgorithms(self):
        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)

        extensionAlias = {
        "python": "py",
        "java": "java",
        "javascript": "js",
        "php": "php",
        }
        
        for codePath in fh.getCodeFilesPath():
            if codePath.split('.')[-1] != extensionAlias[self.language]:
                continue
            sourceCode = fh.readFile(codePath)
            code = CodeProcessor(self.language, sourceCode)
            root = code.getRootNode()

            print("optimized tree")
            self.converter.createDataFlowTree(root, codePath)

            # print("previous tree")
            # astRoot = self.converter.createAstTree(root, codePath)
            # self.converter.addDataFlowEdgesToTree(astRoot)
    
    def insertTreeToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.dataFlowEdges) != 0:
                self.insertNodeToNeo4j(node)

            for child in node.astChildren:
                queue.append(child)

    def insertCompleteTreeToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            self.insertNodeToNeo4j(node)

            for child in node.astChildren:
                queue.append(child)

    def insertDataFlowRelationshipsToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.dataFlowEdges) != 0:
                self.createDataFlowRelationship(node)

            for child in node.astChildren:
                queue.append(child)

    def insertAllRelationshipsToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.dataFlowEdges) != 0:
                self.createDataFlowRelationship(node)
            if len(node.controlFlowEdges) != 0:
                self.createControlFlowRelationship(node)

            for child in node.astChildren:
                queue.append(child)

        self.createASTRelationship()
        
    def insertNodeToNeo4j(self, node: IRNode):
        parameters = {
            "id": node.id,
            "type": node.type,
            "content": node.content,
            "parent_id": node.parentId, 
            "scope": node.scope, 
            "filename": node.filename, 
            "startPoint": node.startPoint,
            "endPoint": node.endPoint,
            "is_source": node.isSource, 
            "is_sink": node.isSink, 
            "is_tainted": node.isTainted, 
            "is_sanitizer": node.isSanitizer
        }

        query = '''CREATE (:Node {
            id: $id, 
            type: $type, 
            content: $content, 
            parent_id: $parent_id, 
            scope: $scope, 
            filename: $filename, 
            startPoint: $startPoint, 
            endPoint: $endPoint, 
            is_source: $is_source, 
            is_sink: $is_sink, 
            is_tainted: $is_tainted, 
            is_sanitizer: $is_sanitizer
            })'''
        
        try:
            self.connection.query(query, parameters, db="connect-python")
        except Exception as e:
            print(f"Query insert node error: {e}")
    
    def createASTRelationship(self):
        query = '''
                MATCH (parent: Node), (child: Node)
                WHERE child.parent_id = parent.id
                CREATE (parent)-[:AST_PARENT_TO]->(child)
            '''
        try:
            self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query create AST relationship error: {e}")

    def createControlFlowRelationship(self, node: IRNode):
        for edge in node.controlFlowEdges:
            parameters = {
                "id": node.id,
                "cfg_parent_id": edge.cfgParentId,
                "statement_order": edge.statementOrder
            }

            query = '''
                    MATCH (child:Node), (parent:Node)
                    WHERE child.id = $id AND parent.id = $cfg_parent_id
                    CREATE (child)<-[r:CONTROL_FLOW_TO{statement_order: $statement_order}]-(parent)
                    SET child:ControlNode
                    SET parent:ControlNode
                '''

            try:
                self.connection.query(query, parameters=parameters, db="connect-python")
            except Exception as e:
                print(f"Query create control flow relationship error: {e}")

    def createDataFlowRelationship(self, node: IRNode):
        for edge in node.dataFlowEdges:
            parameters = {
                    "id": node.id,
                    "dfg_parent_id": edge.dfgParentId,
                    "data_type": edge.dataType
                }
            
            if edge.dataType == "value" or edge.dataType == "reassignment":
                query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = $id AND parent.id = $dfg_parent_id AND ($data_type = 'value' OR $data_type = 'reassignment')
                        MERGE (child)-[r:DATA_FLOW_TO{data_type: $data_type}]->(parent)
                        SET child:DataNode
                        SET parent:DataNode
                    '''
            else:
                query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = $id AND parent.id = $dfg_parent_id AND ($data_type = 'called' OR $data_type = 'referenced')
                        MERGE (parent)-[r:DATA_FLOW_TO{data_type: $data_type}]->(child)
                        SET child:DataNode
                        SET parent:DataNode
                '''

            try:
                self.connection.query(query, parameters=parameters, db="connect-python")
            except Exception as e:
                print(f"Query create data flow relationship error: {e}")
    
    def propagateTaint(self):
        query = '''
            MATCH (source{is_source: True})-[r:DATA_FLOW_TO|CALL*]->(tainted)
            SET tainted.is_tainted=True, tainted:Tainted
            return source, r, tainted
        '''
        self.connection.query(query, db="connect-python")
    
    def appySanitizers(self):
        query = '''
            MATCH (sanitizer{is_sanitizer: True})-[r:DATA_FLOW_TO|CALL*]->(untainted)
            SET untainted.is_tainted=False
            REMOVE untainted:Tainted
            RETURN sanitizer, r, untainted
        '''

        try:
            self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query insert node error: {e}")

    def getPathInjectionVulnerability(self):
        query = '''
            MATCH vuln=(n1:Node {is_source: True})-[:DATA_FLOW_TO*]->(n2:Node {is_sink: True})
            RETURN n1, vuln, n2
        '''
        try:
            return self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query get path injection error: {e}")
    
    def getSourceAndSinkInjectionVulnerability(self):
        query = '''
            MATCH (source:Node {is_source: True})-[:DATA_FLOW_TO*]->(:Node {is_tainted: True})-[:DATA_FLOW_TO]->(sink:Node {is_sink: True})
            RETURN 
            source.content as SourceContent, 
            sink.content as SinkContent, 
            source.filename as SourceFile, 
            sink.filename as SinkFile, 
            source.startPoint as SourceStart, 
            sink.startPoint as SinkStart
        '''
        try:
            return self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query get source and sink injection error: {e}")
    
    def deleteAllNodesAndRelationships(self):
        query = '''
            MATCH (n) DETACH DELETE (n)
        '''
        try:
            return self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query delete all nodes and relationships error: {e}")

    def deleteAllNodesAndRelationshipsByAPOC(self):
        query = '''
            MATCH (n) DETACH DELETE (n)
        '''
        try:
            return self.connection.query(query, db="connect-python")
        except Exception as e:
            print(f"Query delete all nodes and relationships error: {e}")