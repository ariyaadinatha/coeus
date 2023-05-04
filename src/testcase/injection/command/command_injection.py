import shlex
import subprocess

address = input()
command = "ping -c 1 {}".format(address)

# vuln
subprocess.Popen(command, shell=True)

# safe
args = shlex.split(command)
subprocess.Popen(args)