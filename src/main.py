from handler.dependency.dependencyhandler import DependencyHandler, Dependency
from handler.secret.secrethandler import SecretDetection
from utils.vulnhandler import VulnerableHandler
from utils.codehandler import FileHandler
from utils.codehandler import Code
from utils.log import logger
from utils.intermediate_representation.converter import IRConverter
import time
import click

@click.group()
def cli():
    pass

@click.command(short_help='Scan code for dependencies vulnerabilities')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def dependency(path, output):
    try:
        fh = FileHandler()
        dh = DependencyHandler()
        fh.getAllFilesFromRepository(path)
        fh.getDependencies(dh)
        dh.scanDependencies()
        ### TO DO ADD ANOTHER OPTIONS OF OUTPUT
        dh.dumpVulnerabilities()
    except Exception as e:
        logger.error(f"Error : {repr(e)}")
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
            "php": "php",
            # "ts": "typescript"
        }
        try:
            sourceCode = fh.readFile(codePath)
            code = Code(extensionAlias[codeExtension], sourceCode)
        except Exception as e:
            logger.error(f"Error : {repr(e)}")

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
            logger.error(f"Error : {repr(e)}")

    fileNameOutput = path.split("/")[-1]
    vh.dumpVulnerabilities(fileNameOutput)

cli.add_command(secret)

@click.command(short_help='Scan code for injection vulnerability')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def injection(path, output):
    fh = FileHandler()
    fh.getAllFilesFromRepository("./testcase/graph")
    for codePath in fh.getCodeFilesPath():
        sourceCode = fh.readFile(codePath)
        code = Code("python", sourceCode)

        root = code.getRootNode()

        # ***: export tree to CSV
        # code.traverseTree(root, [])
        # code.createTreeListWithId(root, code.treeList, "parent")
        # code.exportToCSV()

        # ***: convert node to IR
        converter = IRConverter()
        astRoot = converter.createCompleteTree(root, codePath)

        print("tree")
        converter.printTree(astRoot)     
        converter.exportAstToCsv(astRoot)
cli.add_command(injection)

@click.command(short_help='Scan code for broken access control')
@click.option('--path', '-p', help='Path to source code')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'html', 'pdf']), help='Specifies the output format or file results.')
def access():
    pass
cli.add_command(access)

if __name__ == "__main__":
    # dependencyVulnExample()
    # getDependency()
    # parseLanguage()
    # secretDetection()

    # logger.info("=============== Starting coeus ===============")
    # startTime = time.time()
    cli()
    # logger.info(f"Execution time: {(time.time() - startTime)}")
    # logger.info("=============== Successfully running coeus ===============")