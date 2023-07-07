import subprocess

def test(request):
    test = request.POST.get('domain')
    return test

def sink(request):
    command = test(request)
    process = subprocess.Popen(command, shell=True)