from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.secret.secrethandler import SecretDetection
from handler.injection.injectionhandler import InjectionHandler
from utils.vulnhandler import VulnerableHandler
from utils.codehandler import FileHandler
from utils.codehandler import CodeProcessor
from utils.log import logger
from utils.intermediate_representation.converter import IRConverter
from dotenv import load_dotenv
import os
import time
import click

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
        handler = InjectionHandler("./testcase/injection/command", language)
        handler.taintAnalysis()
    except Exception as e:
        print("Failed to do taint analysis:", e)

    logger.info(f"Execution time: {(time.time() - startTime)}")
    logger.info("=============== Finished injection detection ===============")

cli.add_command(injection)

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

load_dotenv()
if __name__ == "__main__":
    cli()