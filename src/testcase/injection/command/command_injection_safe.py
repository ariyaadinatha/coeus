import shlex
import subprocess

address = input()
command = "ping -c 1 {}".format(address)
args = shlex.split(command)
subprocess.Popen(args)