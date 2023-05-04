from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.secret.secrethandler import SecretDetection
from handler.injection.injectionhandler import InjectionHandler
from utils.intermediate_representation.converter import IRConverter
from utils.vulnhandler import VulnerableHandler, Vulnerable
from utils.codehandler import FileHandler
from utils.codehandler import CodeProcessor
from utils.log import logger
from dotenv import load_dotenv
from datetime import datetime
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
def dependency(path, output):
    logger.info("=============== Starting dependency detection ===============")
    startTime = time.time()

    try:
        fh = FileHandler()
        dh = DependencyHandler()
        fh.getAllFilesFromRepository(path)
        fh.getDependencies(dh)

        # get all path
        for code in fh.getCodeFilesPath():
            dh.scanDependenciesUsingRegex(code)
        
        dh.scanDependencies()
        dh.dumpVulnerabilities()



    except Exception as e:
        logger.error(f"Error : {repr(e)}")

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished dependency detection ===============")

cli.add_command(dependency)

@click.command(short_help='Scan code for hardcoded secret')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def secret(path, output):
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
def injection(path, language, output):
    logger.info("=============== Starting injection detection ===============")
    startTime = time.time()

    handler = InjectionHandler("./testcase/injection/command", language)
    handler.compareDataFlowAlgorithms()

    # try:
    #     handler = InjectionHandler("./testcase/injection/command", language)
    #     # handler = InjectionHandler("../../flask-simple-app", language)
    #     result = handler.taintAnalysis()
    #     vulnHandler = VulnerableHandler()

    #     for res in result:
    #             vuln = Vulnerable(
    #                 "Injection vulnerability", 
    #                 "application is vulnerable to unsafe input injection", 
    #                 "A03:2021", 
    #                 "High", 
    #                 None, 
    #                 f"Input from {res['SourceContent']} could be passed to {res['SinkContent']} without going through sanitization process", 
    #                 f"{res['SourceFile']} and {res['SinkFile']}", 
    #                 f"{res['SourceStart']} and {res['SinkStart']}", 
    #                 datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    #                 )
    #             print(vuln)
    #             vulnHandler.addVulnerable(vuln)
        
    #     fileNameOutput = path.split("/")[-1]
    #     vulnHandler.dumpVulnerabilities("result")
    # except Exception as e:
    #     print("Failed to do taint analysis:", e)

    executionTime = time.time() - startTime
    print(executionTime)
    logger.info(f"Execution time: {executionTime}")
    logger.info("=============== Finished injection detection ===============")

cli.add_command(injection)

@click.command(short_help='Scan code for broken access control')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def access():
    logger.info("=============== Starting broken access detection ===============")
    startTime = time.time()

    # code here

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished broken access detection ===============")
cli.add_command(access)

if __name__ == "__main__":
    cli()