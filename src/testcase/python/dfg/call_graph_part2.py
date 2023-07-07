import subprocess

def sink(command):
    process = subprocess.Popen(command, shell=True)