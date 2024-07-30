def func1():
    return "value func1"

def func2():
    return "value func2"

a = "value a"
b = "value b"

if a == "value a":
    if b == "value b":
        a = "value aa"
    else:
        a = func1()
elif a == "value aa":
    print(a)
else:
    a = func2()