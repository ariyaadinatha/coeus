from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.secret.secrethandler import SecretDetection
from utils.vulnhandler import VulnerableHandler
from utils.codehandler import FileHandler
from utils.codehandler import Code
from utils.log import logger
import time
import click

@click.group()
def cli():
    pass

@click.command(short_help='Scan code for dependencies vulnerabilities')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def dependency(path, output):
    fh = FileHandler()
    dh = DependencyHandler()
    fh.getAllFilesFromRepository(path)
    fh.getDependencies(dh)
    dh.scanDependencies()
    ### TO DO ADD ANOTHER OPTIONS OF OUTPUT
    dh.dumpVulnerabilities()
cli.add_command(dependency)

@click.command(short_help='Scan code for hardcoded secret')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def secret(path, output):
    fh = FileHandler()
    fh.getAllFilesFromRepository(path)
    sc = SecretDetection()
    vh = VulnerableHandler()
    for codePath in fh.getCodeFilesPath():
        codeExtension = codePath.split(".")[-1]
        extensionAlias = {
            "py": "python",
            "java": "java",
            "js": "javascript",
            "php": "php"
        }
        sourceCode = fh.readFile(codePath)
        code = Code(extensionAlias[codeExtension], sourceCode)

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

    vh.dumpVulnerabilities("vulnerable")
            # pass

cli.add_command(secret)

@click.command(short_help='Scan code for injection vulnerability')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def injection():
    pass
cli.add_command(injection)

@click.command(short_help='Scan code for broken access control')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def access():
    pass
cli.add_command(access)

if __name__ == "__main__":
    # logger.info("=============== Starting coeus ===============")
    # startTime = time.time()
    cli()
    # logger.info(f"Execution time: {(time.time() - startTime)}")
    # logger.info("=============== Successfully running coeus ===============")