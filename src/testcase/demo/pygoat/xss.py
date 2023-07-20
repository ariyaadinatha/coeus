def xss_lab2(request):
    if request.user.is_authenticated:
        
        username = request.POST.get('username', '')
        if username:
            username = username.strip()
            username = username.replace("<script>", "").replace("</script>", "")
        else:
            username = "Guest"
        context = {
        'username': username
                }
        return render(request, 'Lab/XSS/xss_lab_2.html', context)
    else:
        return redirect('login')