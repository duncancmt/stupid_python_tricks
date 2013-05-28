from inspect import getargspec

class UndefinedArityError(Exception):
    def __str__(self):
        return "Tried to automatically curry a function with * or * args"

def curry(fn, numargs = 0):
    """Currys a function
Returns a new function that, when called, will return either:
1) the value of the given function applied to the given arguments (if there are
     enough arguments to satisfy the function)
=== OR ===
2) the given function curried over the originally curried arguments and the
     newly given arguments (if there are not enough arguments to satisfy the
     function)
When too many arguments are supplied, the extra arguments are discarded.
Keyword arguments will never be discarded. Newly supplied keyword arguments will
shadow older arguments.

Arguments:
fn -> the function to be curried
numargs = 0 -> the number of arguments that will satisfy the function to be
     curried. If numargs is 0, curry extracts the number of arguments from
     introspection. If numargs is 0 and the function has a * or ** argument,
     curry will raise a UndefinedArityError."""
    if numargs == 0:
        argspec = getargspec(fn)
        if not (argspec[1] == None and argspec[2] == None):
            raise UndefinedArityError
        numargs = len(argspec[0])

    def curry_helper(*given,**givenkeys):
        def curried_fn(*supplied,**suppliedkeys):
            numargsgiven = len(given)+len(supplied)+len(givenkeys)+len(suppliedkeys)
            new = list(given)
            new.extend(supplied)
            newkeys = givenkeys.copy()
            newkeys.update(suppliedkeys)

            if numargsgiven < numargs:
                return curry_helper(*new,**newkeys)
            elif numargsgiven == numargs:
                return fn( *new, **newkeys )
            else:
                return fn(*new[:(numargs - numargsgiven)], **newkeys )

        return curried_fn
    return curry_helper()
