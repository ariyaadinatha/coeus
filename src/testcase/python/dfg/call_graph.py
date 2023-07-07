import subprocess

def test(request):
    test = request.POST.get('domain')
    sink(test)

def sink(command):
        process = subprocess.Popen(command, shell=True)