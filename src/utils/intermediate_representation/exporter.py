from pathlib import Path
import csv
from utils.intermediate_representation.nodes.nodes import IRNode

class IRExporter():
    def __init__(self) -> None:
        pass
    
    def exportTreeToCsvFiles(self, root: IRNode, exportPath: str):
        self.exportAstNodesToCsv(root, exportPath)
        self.exportDfgEdgesToCsv(root, exportPath)
        self.exportCfgEdgesToCsv(root, exportPath)
    
    def exportAstNodesToCsv(self, root: IRNode, exportPath: str):
        header = [
                'id', 
                'type', 
                'content', 
                'parent_id', 
                'scope', 
                'start_point',
                'end_point',
                'is_source', 
                'is_sink', 
                'is_tainted',
                'is_sanitizer',
                ]
        
        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_nodes.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                row = [
                    node.id, 
                    node.type, 
                    node.content, 
                    node.parentId, 
                    node.scope, 
                    node.startPoint,
                    node.endPoint,
                    node.isSource,
                    node.isSink,
                    node.isTainted,
                    node.isSanitizer,
                    ]
                writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)
    
    def exportDfgEdgesToCsv(self, root: IRNode, exportPath: str):
        header = ['id', 'dfg_parent_id', 'data_type']

        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_dfg_edges.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.dataFlowEdges:
                    row = [node.id, edge.dfgParentId, edge.dataType]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)
    
    def exportCfgEdgesToCsv(self, root: IRNode, exportPath: str):
        header = ['id', 'cfg_parent_id', 'statement_order']

        # setup file and folder
        basename = self.getExportBasename(exportPath)
        Path(f"./csv/{basename}").mkdir(parents=True, exist_ok=True)

        with open(f'./csv/{basename}/{basename}_cfg_edges.csv', 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            queue: list[IRNode] = [root]

            while queue:
                node = queue.pop(0)

                for edge in node.controlFlowEdges:
                    row = [node.id, edge.cfgParentId, edge.statementOrder]
                    writer.writerow(row)

                for child in node.astChildren:
                    queue.append(child)

    def getExportBasename(self, filename: str) -> str:
        if len(filename.split("\\")) >= 2:
            basename = filename.split("\\")[-1].replace("/", "-").replace("\\", "-")
            if basename[0] == "-":
                basename = basename[1:]
        
            return basename
        return filename