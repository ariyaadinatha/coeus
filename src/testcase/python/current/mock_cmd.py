if(request.method=="POST"):
  domain=request.POST.get('domain')
  domain=domain.replace("https://www.",'')
  os=request.POST.get('os')
  print(os)
  if(os=='win'):
      command = "nslookup {}".format(domain)
  else:
      command = "dig {}".format(domain)

  process = subprocess.Popen(
      command,
      shell=True)