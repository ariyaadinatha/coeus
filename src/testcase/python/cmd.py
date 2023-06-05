# not solved, because of pattern a = a.replace() where a is tainted
def cmd_lab(request):
    if request.user.is_authenticated:
        if(request.method=="POST"):
            domain=request.POST.get('domain')
            domain=domain.replace("https://www.",'')
            os=request.POST.get('os')
            print(os)
            if(os=='win'):
                command="nslookup {}".format(domain)
            else:
                command = "dig {}".format(domain)
            
            try:
                # output=subprocess.check_output(command,shell=True,encoding="UTF-8")
                process = subprocess.Popen(
                    command,
                    shell=True)
                stdout, stderr = process.communicate()
                data = stdout.decode('utf-8')
                stderr = stderr.decode('utf-8')
                # res = json.loads(data)
                # print("Stdout\n" + data)
                output = data + stderr
                print(data + stderr)
            except:
                output = "Something went wrong"
                return render(request,'Lab/CMD/cmd_lab.html',{"output":output})
            print(output)
            return render(request,'Lab/CMD/cmd_lab.html',{"output":output})
        else:
            return render(request, 'Lab/CMD/cmd_lab.html')
    else:
        return redirect('login')

# success
# def cmd_lab2(request):
#     if request.user.is_authenticated:
#         if (request.method=="POST"):
#             val=request.POST.get('val')
            
#             print(val)
#             try:
#                 output = eval(val)
#             except:
#                 output = "Something went wrong"
#                 return render(request,'Lab/CMD/cmd_lab2.html',{"output":output})
#             print("Output = ", output)
#             return render(request,'Lab/CMD/cmd_lab2.html',{"output":output})
#         else:
#             return render(request, 'Lab/CMD/cmd_lab2.html')
#     else:
#         return redirect('login')