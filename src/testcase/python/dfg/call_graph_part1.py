from call_graph_part2 import sink

def test(request):
    test = request.POST.get('domain')
    sink(test)