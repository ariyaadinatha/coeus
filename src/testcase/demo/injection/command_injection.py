import subprocess
import shlex

# ex: test && ls
command = input()
build_command = f"echo {command}"
safe_command = f"echo {shlex.split(command)}"

print("vuln command", build_command)
print("safe command", shlex.split(command))

# Vulnerable
print("executing vuln command")
subprocess.run(build_command, shell=True)

# Safe
print("executing safe command")
subprocess.run(safe_command, shell=True)