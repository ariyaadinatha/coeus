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
import traceback
import os
import json

class InjectionHandler:
    def __init__(self, projectPath: str, language: str):
        try:
            self.connection = Neo4jConnection(os.getenv('DB_URI'), os.getenv('DB_USER'), os.getenv('DB_PASS'))
        except Exception as e:
            print("Failed to create the driver:", e)
        
        self.dbName = os.getenv('DB_NAME')
        self.vulnHandler = VulnerableHandler()
        self.projectPath = projectPath
        self.language = language
        self.loadSourceSinkAndSanitizer()
        self.converter = self.createConverter()

    def createConverter(self) -> IRConverter:
        if self.language == "python":
            return IRPythonConverter(self.sources, self.sinks, self.sanitizers)
        elif self.language == "javascript":
            return IRJavascriptConverter(self.sources, self.sinks, self.sanitizers)
        elif self.language == "php":
            return IRPhpConverter(self.sources, self.sinks, self.sanitizers)
        elif self.language == "java":
            return IRJavaConverter(self.sources, self.sinks, self.sanitizers)

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
            astRoot = self.converter.createDataFlowTreeDFS(root, codePath)
            self.insertTreeToNeo4j(astRoot)
            self.insertDataFlowRelationshipsToNeo4j(astRoot)
            self.setLabels()

    def buildAstTree(self, fileHandler: FileHandler, codePath: str) -> IRNode:
        sourceCode = fileHandler.readFile(codePath)
        code = CodeProcessor(self.language, sourceCode)
        root = code.getRootNode()
        astRoot = self.converter.createAstTree(root, codePath.rsplit('.', 1)[0])
        self.converter.registerFunctionsToSymbolTable(astRoot)

        return astRoot

    def buildCompleteTree(self, fileHandler: FileHandler, codePath: str):
        sourceCode = fileHandler.readFile(codePath)
        code = CodeProcessor(self.language, sourceCode)
        root = code.getRootNode()
        astRoot = self.converter.createCompleteTree(root, codePath)
        self.insertAllNodesToNeo4j(astRoot)
        self.insertDataFlowAndControlFlowRelationshipsToNeo4j(astRoot)

    def buildCompleteProject(self):
        fh = FileHandler()
        fh.getAllFilesFromRepository(self.projectPath)
        
        for codePath in fh.getCodeFilesPath():
                if codePath.split('.')[-1] != EXTENSION_ALIAS[self.language]:
                    continue

                self.buildCompleteTree(fh, codePath)

    def taintAnalysis(self) -> Path:
        try:
            result = []
            roots = []
            
            self.createUniqueConstraint()
            self.deleteAllNodesAndRelationshipsByAPOC()
            
            fh = FileHandler()
            fh.getAllFilesFromRepository(self.projectPath)

            for codePath in fh.getCodeFilesPath():
                if codePath.split('.')[-1] != EXTENSION_ALIAS[self.language]:
                    continue
            
                astRoot = self.buildAstTree(fh, codePath)
                roots.append(astRoot)
                self.insertAllNodesToNeo4j(astRoot)
            
            for root in roots:
                self.converter.addControlFlowEdgesToTree(root)
                self.converter.addDataFlowEdgesToTree(root)
                self.insertDataFlowAndControlFlowRelationshipsToNeo4j(root)

                root.printChildren()

            self.createASTRelationship()
            self.setLabels()
            result = self.expandInjectionPathUsingAPOC()

            return result
        except Exception as e:
            print(traceback.print_exc())
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

    def insertAllNodesToNeo4j(self, root: IRNode):
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

    def insertDataFlowAndControlFlowRelationshipsToNeo4j(self, root: IRNode):
        queue: list[IRNode] = [root]

        while len(queue) != 0:
            node = queue.pop(0)

            if len(node.dataFlowEdges) != 0:
                self.createDataFlowRelationship(node)
            if len(node.controlFlowEdges) != 0:
                self.createControlFlowRelationship(node)

            for child in node.astChildren:
                queue.append(child)

    def createUniqueConstraint(self):
        query = '''
            CREATE CONSTRAINT FOR (n:Node) REQUIRE n.id IS UNIQUE
        '''

        try:
            print("creating unique constraint for id")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query create constraint error: {traceback.print_exc()}")

    def setLabels(self):
        self.setRootLabel()
        self.setSourceLabel()
        self.setSanitizerLabel()
        self.setSinkLabel()

    def setRootLabel(self):
        query = '''
            MATCH (n) WHERE n.parent_id IS NULL
            SET n:Root
        '''

        try:
            print("setting root label")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query set root label error: {traceback.print_exc()}")

    def setSourceLabel(self):
        query = '''
            MATCH (n:Node)
            WHERE n.is_source = true
            SET n:Source
        '''

        try:
            print("setting source label")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query set root label error: {traceback.print_exc()}")
    
    def setSinkLabel(self):
        query = '''
            MATCH (n:Node)
            WHERE n.is_sink = true
            SET n:Sink
        '''

        try:
            print("setting sink label")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query set root label error: {traceback.print_exc()}")
        
    def setSanitizerLabel(self):
        query = '''
            MATCH (n:Node)
            WHERE n.is_sanitizer = true
            SET n:Sanitizer
        '''

        try:
            print("setting sanitizer label")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query set root label error: {traceback.print_exc()}")

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
            print("inserting node")
            self.connection.query(query, parameters, db=self.dbName)
        except Exception as e:
            print(f"Query insert node error: {traceback.print_exc()}")
    
    def createASTRelationship(self):
        query = '''
                MATCH (parent: Node), (child: Node)
                WHERE child.parent_id = parent.id
                CREATE (parent)-[:AST_PARENT_TO]->(child)
            '''
        try:
            print("creating AST relationship")
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query create AST relationship error: {traceback.print_exc()}")

    def createControlFlowRelationship(self, node: IRNode):
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

    def createDataFlowRelationship(self, node: IRNode):
        for edge in node.dataFlowEdges:
            parameters = {
                    "id": node.id,
                    "dfg_parent_id": edge.dfgParentId,
                    "data_type": edge.dataType
                }
            
            if edge.dataType == "value" or edge.dataType == "passed":
                query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = $id AND parent.id = $dfg_parent_id AND ($data_type = 'value' OR $data_type = 'reassignment' OR $data_type = 'passed')
                        MERGE (child)-[r:DATA_FLOW_TO{data_type: $data_type}]->(parent)
                        SET child:DataNode
                        SET parent:DataNode
                    '''
            else:
                query = '''
                        MATCH (child:Node), (parent:Node)
                        WHERE child.id = $id AND parent.id = $dfg_parent_id AND ($data_type = 'called' OR $data_type = 'referenced' OR $data_type = 'returned')
                        MERGE (parent)-[r:DATA_FLOW_TO{data_type: $data_type}]->(child)
                        SET child:DataNode
                        SET parent:DataNode
                '''

            try:
                print("creating data flow relationship")
                self.connection.query(query, parameters=parameters, db=self.dbName)
            except Exception as e:
                print(f"Query create data flow relationship error: {traceback.print_exc()}")

    def expandInjectionPathUsingAPOC(self):
        query = '''
            MATCH (source:Node {is_source: True})
            WITH collect(source) AS startNodes
            MATCH (end:Node {is_sink: True})
            WITH startNodes, collect(end) AS endNodes
            OPTIONAL MATCH (blacklist:Node {is_sanitizer: True })
            WITH startNodes, endNodes, collect(blacklist) AS blacklistNodes
            CALL apoc.path.expandConfig(startNodes, {endNodes: endNodes, blacklistNodes: blacklistNodes, relationshipFilter: 'DATA_FLOW_TO>'})
            YIELD path
            RETURN path
        '''

        try:
            print("expanding injection path using APOC")
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query expand path using APOC error: {traceback.print_exc()}")

    def getSinkInjectionUsingAPOC(self):
        query = '''
            MATCH (source:Node {is_source: True})
            WITH collect(source) AS startNodes
            MATCH (terminator:Node {is_sink: True})
            WITH startNodes, collect(terminator) AS terminatorNodes
            MATCH (blacklist:Node {is_sanitizer: True })
            WITH startNodes, terminatorNodes, collect(blacklist) AS blacklistNodes
            CALL apoc.path.subgraphNodes(startNodes, {terminatorNodes: terminatorNodes, blacklistNodes: blacklistNodes, relationshipFilter: 'DATA_FLOW_TO>', bfs: False, includeStartNode: True})
            YIELD node
            RETURN node
        '''

        try:
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query get sink injection using APOC error: {traceback.print_exc()}")
    
    def propagateTaint(self):
        query = '''
            MATCH (source{is_source: True})-[r:DATA_FLOW_TO*]->(tainted)
            SET tainted.is_tainted=True, tainted:Tainted
            return source, r, tainted
        '''
        self.connection.query(query, db=self.dbName)
    
    def applySanitizers(self):
        query = '''
            MATCH (sanitizer{is_sanitizer: True})-[r:DATA_FLOW_TO]->(untainted)
            SET untainted.is_tainted=False
            REMOVE untainted:Tainted
            RETURN sanitizer, r, untainted
        '''

        try:
            self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query insert node error: {traceback.print_exc()}")

    def getPathInjectionVulnerability(self):
        query = '''
            MATCH vuln=(n1:Node {is_source: True})-[:DATA_FLOW_TO*]->(n2:Node {is_sink: True})
            RETURN n1, vuln, n2
        '''
        try:
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query get path injection error: {traceback.print_exc()}")
    
    def getSourceAndSinkInjectionVulnerability(self):
        query = '''
            MATCH (source:Node {is_source: True})-[:DATA_FLOW_TO*]->(:Node {is_tainted: True})-[:DATA_FLOW_TO]->(sink:Node {is_sink: True})
            RETURN 
            source.id as SourceId,
            sink.id as SinkId,
            source.content as SourceContent, 
            sink.content as SinkContent, 
            source.filename as SourceFile, 
            sink.filename as SinkFile, 
            source.startPoint as SourceStart, 
            sink.startPoint as SinkStart
        '''
        try:
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query get source and sink injection error: {traceback.print_exc()}")
    
    def deleteAllNodesAndRelationships(self):
        query = '''
            MATCH (n) DETACH DELETE (n)
        '''
        try:
            print("deleting all nodes and relationship")
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query delete all nodes and relationships error: {traceback.print_exc()}")

    def deleteAllNodesAndRelationshipsByAPOC(self):
        query = '''
            CALL apoc.periodic.iterate('MATCH (n) RETURN n', 'DETACH DELETE n', {batchSize:1000})
        '''
        try:
            print("deleting all nodes and relationship using APOC")
            return self.connection.query(query, db=self.dbName)
        except Exception as e:
            print(f"Query delete all nodes and relationships error: {traceback.print_exc()}")