test = input()

another_test = test

test = "change test"

# safe
eval(test)
# vulnerable
eval(another_test)