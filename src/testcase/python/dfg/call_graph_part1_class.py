from call_graph_part2_class import Example

def test(request):
    test = request.POST.get('domain')
    Example.sink(test, "bukan injection")