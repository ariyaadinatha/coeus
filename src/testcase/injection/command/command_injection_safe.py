import shlex
import subprocess

address = request.args.get("address")
command = "ping -c 1 {}".format(address)
args = shlex.split(command)
subprocess.Popen(args)