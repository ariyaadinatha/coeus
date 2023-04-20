address = request.args.get("address")
# command injection
# ex: google.com ; ls -la
cmd = "ping -c 1 %s" % address
subprocess.Popen(cmd, shell=True)