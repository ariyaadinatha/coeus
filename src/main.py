from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.secret.secrethandler import SecretDetection
from handler.injection.injectionhandler import InjectionHandler
from utils.intermediate_representation.converter.converter import IRConverter
from utils.vulnhandler import VulnerableHandler, Vulnerable
from utils.codehandler import FileHandler
from utils.codehandler import CodeProcessor
from utils.log import logger
from dotenv import load_dotenv
from datetime import datetime
from neo4j.graph import Path
import traceback
import time
import click

# setup global variable
load_dotenv()

@click.group()
def cli():
    pass

@click.command(short_help='Scan code for dependencies vulnerabilities')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
@click.option('--mode', '-m', default='medium', type=click.Choice(['low', 'medium', 'high']), help='Specifies the scan sensitivity.')
def dependency(path, output, mode):
    logger.info("=============== Starting dependency detection ===============")
    startTime = time.time()

    try:
        fh = FileHandler()
        dh = DependencyHandler()
        fh.getAllFilesFromRepository(path)
        fh.getDependencies(dh, mode)

        # get all path
        if mode == "high":
            for code in fh.getCodeFilesPath():
                dh.scanDependenciesUsingRegex(code)
        
        fileNameOutput = path.split("/")[-1]
        dh.scanDependencies(mode)
        dh.dumpVulnerabilities(fileNameOutput)

    except Exception as e:
        logger.error(f"Error : {repr(e)}")

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished dependency detection ===============")

cli.add_command(dependency)

@click.command(short_help='Scan code for hardcoded secret')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
@click.option('--mode', '-m', default='medium', type=click.Choice(['low', 'medium', 'high']), help='Specifies the scan sensitivity.')
def secret(path, output, mode):
    logger.info("=============== Starting secret detection ===============")
    startTime = time.time()

    fh = FileHandler()
    fh.getAllFilesFromRepository(path)
    sc = SecretDetection()
    vh = VulnerableHandler()

    logger.info("Scanning secret...")
    for codePath in fh.getCodeFilesPath():
        codeExtension = codePath.split(".")[-1]
        extensionAlias = {
            "py": "python",
            "java": "java",
            "js": "javascript",
            "php": "php",
        }
        try:
            sourceCode = fh.readFile(codePath)
        except Exception as e:
            logger.error(f"Readfile error : {repr(e)}, param: {codePath}")

        try:
            code = CodeProcessor(extensionAlias[codeExtension], sourceCode)
        except Exception as e:
            logger.error(f"Code processing error : {repr(e)}")

        try:
            if codeExtension == "py":
                # variable, list
                code.searchTree(code.getRootNode(), "assignment", sc.getAssignmentList())
                # function
                code.searchTree(code.getRootNode(), "call", sc.getAssignmentList())

            if codeExtension == "java":
                # variable, array
                code.searchTree(code.getRootNode(), "variable_declarator", sc.getAssignmentList())
                # function
                code.searchTree(code.getRootNode(), "method_invocation", sc.getAssignmentList())

            # if codeExtension == "js" or codeExtension == "ts":
            if codeExtension == "js":
                # variable, array
                code.searchTree(code.getRootNode(), "variable_declarator", sc.getAssignmentList())
                # function
                code.searchTree(code.getRootNode(), "call_expression", sc.getAssignmentList())

            if codeExtension == "php":
                # variable, array
                code.searchTree(code.getRootNode(), "assignment_expression", sc.getAssignmentList())
                # function
                code.searchTree(code.getRootNode(), "function_call_expression", sc.getAssignmentList())

            # Secret Detection
            sc.valueDetection(code.getSourceCode(), vh, codePath)
            sc.clearAssignmentList()
        except Exception as e:
            logger.error(f"Error: {repr(e)}, parameter: {codePath}")

    fileNameOutput = path.split("/")[-1]
    vh.dumpVulnerabilities(fileNameOutput)

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished secret detection ===============")

cli.add_command(secret)

@click.command(short_help='Scan code for injection vulnerability')
@click.option('--path', '-p', help='Path to source code')
@click.option('--language', '-l', default='python', type=click.Choice(['python', 'javascript', 'java', 'php']), help='Determines the language used by the to-be-analyzed project')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
@click.option('--mode', '-m', default='medium', type=click.Choice(['low', 'medium', 'high']), help='Specifies the scan sensitivity.')
def injection(path, language, output, mode):
    logger.info("=============== Starting injection detection ===============")
    startTime = time.time()

    try:
        '''
        current
        '''
        # handler = InjectionHandler("./testcase/python/current", "python")
        # handler = InjectionHandler("./testcase/php/current", "php")
        # handler = InjectionHandler("./testcase/java/current", "java")
        handler = InjectionHandler("./testcase/javascript/current", "javascript")

        '''
        testing
        '''
        # handler = InjectionHandler("../../DVWA", language)
        # handler = InjectionHandler("../../PyGoat", language)
        # handler = InjectionHandler("../../NodeGoat", "javascript")
        # handler = InjectionHandler("./../../WebGoat", "java")
        
        '''
        testing tito
        '''
        # handler = InjectionHandler("../../coeus-test-projects/DVWA", "php")
        # handler = InjectionHandler("../../coeus-test-projects/PyGoat", "python")
        # handler = InjectionHandler("../../coeus-test-projects/NodeGoat", "javascript")
        # handler = InjectionHandler("./../../coeus-test-projects/WebGoat", "java")
    
        result = handler.taintAnalysis()
        vulnHandler = VulnerableHandler()

        finalRes = set()
        for record in result:
            pathResult: Path = record["path"]
            startNode = pathResult.start_node
            endNode = pathResult.end_node

            key = (startNode.element_id, endNode.element_id)
            if key not in finalRes:
                finalRes.add(key)
                vuln = Vulnerable(
                    "Injection vulnerability", 
                    "application is vulnerable to unsafe input injection", 
                    "A03:2021", 
                    "High", 
                    None, 
                    f"Input from {startNode['content']} could be passed to {endNode['content']} without going through sanitization process", 
                    f"{startNode['filename']} and {endNode['filename']}", 
                    # compensate for row and col starting value 0
                    f"{[startNode['startPoint'][0]+1, startNode['startPoint'][1]+1]} and {[endNode['startPoint'][0]+1, endNode['startPoint'][1]+1]}", 
                    datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                    )
                print(vuln)
                vulnHandler.addVulnerable(vuln)
            
        vulnHandler.dumpVulnerabilities("result")
    except Exception as e:
        print("Failed to do taint analysis")
        print(traceback.print_exc())

    executionTime = time.time() - startTime
    print(f"Execution time: {executionTime}")
    logger.info(f"Execution time: {executionTime}")
    logger.info("=============== Finished injection detection ===============")

cli.add_command(injection)

@click.command(short_help='Build complete tree of source code')
@click.option('--path', '-p', help='Path to source code')
@click.option('--language', '-l', default='python', type=click.Choice(['python', 'javascript', 'java', 'php']), help='Determines the language used by the to-be-analyzed project')
def buildCompleteProject(path, language):
    handler = InjectionHandler(path, language)
    handler.deleteAllNodesAndRelationshipsByAPOC()
    handler.buildCompleteProject()

cli.add_command(buildCompleteProject, name="build-complete")

@click.command(short_help='Build data flow tree of source code')
@click.option('--path', '-p', help='Path to source code')
@click.option('--language', '-l', default='python', type=click.Choice(['python', 'javascript', 'java', 'php']), help='Determines the language used by the to-be-analyzed project')
def buildDataFlowTree(path, language, output, mode):
    handler = InjectionHandler("./testcase/injection/taint_analysis", language)
    handler.deleteAllNodesAndRelationshipsByAPOC()
    handler.buildDataFlowTree()

cli.add_command(buildDataFlowTree, name="build-data-flow")

@click.command(short_help='Scan code for broken access control')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
@click.option('--mode', '-m', default='medium', type=click.Choice(['low', 'medium', 'high']), help='Specifies the scan sensitivity.')
def access(path, output, mode):
    logger.info("=============== Starting broken access detection ===============")
    startTime = time.time()

    # code here

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished broken access detection ===============")
cli.add_command(access)

if __name__ == "__main__":
    cli()