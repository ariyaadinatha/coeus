import shlex
import subprocess

address = input()
command = "ping -c 1 {}".format(address)

real_command = command
command = "google.com"

# safe
subprocess.Popen(command, shell=True)

# vuln
subprocess.Popen(real_command, shell=True)

# safe
args = shlex.split(real_command)
subprocess.Popen(args, shell=True)