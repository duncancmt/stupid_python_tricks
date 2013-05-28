import inspect
import dis
import operator
import sys

function = type(lambda : None) # function(code, globals[, name[, argdefs[, closure]]])
code = type((lambda : None).func_code) # code(argcount, nlocals, stacksize, flags, codestring, constants, names,
                                       #      varnames, filename, name, firstlineno, lnotab[, freevars[, cellvars]])


class TailRecursionException(Exception):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

def opname(op):
    if isinstance(op,str) and len(op) == 1:
        op = ord(op)
    assert isinstance(op, int)
    return dis.opname[op]

def has_arg(op):
    return op >= dis.HAVE_ARGUMENT

def group_args(bytecodes):
    retval = list()
    bytecodes = map(lambda x: x if isinstance(x, int) else ord(x), bytecodes)
    i = 0
    args = list()
    index = None
    while i < len(bytecodes):
        op = bytecodes[i]
        if has_arg(op):
            args = [bytecodes[i+1], bytecodes[i+2]] + args
            i += 3
            if op != dis.EXTENDED_ARG:
                first_op_index = i - len(args)/2*3
                arg_num = reduce(operator.add, map(lambda (i, n): n << (8*i), enumerate(args)))
                args = list()
            else:
                continue
        else:
            first_op_index = i
            arg_num = None
            i += 1
        retval.append((first_op_index, opname(op), arg_num))
    return retval

def tailcall_optimized(only_tail_calls=False):
    def decorator(f):
        assert inspect.isfunction(f)
        instructions = group_args(f.func_code.co_code)
        potential_tail_calls = list()
        last_instruction = None
        for (i, (index, instruction, arg)) in enumerate(instructions):
            if last_instruction == 'CALL_FUNCTION' \
               and instruction == 'RETURN_VALUE':
                potential_tail_calls.append(i)


        raise NotImplementedError

        if only_tail_calls:
            def decorated_inner(*args, **kwargs):
                frame = sys._getframe()
                if frame.f_back and frame.f_back.f_back \
                       and frame.f_code == frame.f_back.f_back.f_code:
                    raise TailRecursionException(args, kwargs)
                else:
                    while True:
                        try:
                            return f(*args, **kwargs)
                        except TailRecursionException as e:
                            args = e.args
                            kwargs = e.kwargs

            # ensure that we preserve the function signature for inspection
            decorated_argspec = inspect.formatargspec(*inspect.getargspec(f))
            decorated_code = compile("def decorated%s:\n    return decorated_inner%s\n" % (decorated_argspec, decorated_argspec),
                                     __file__, "exec")
            decorated = function(decorated_code, {'decorated_inner':decorated_inner}, f.func_name)
            decorated.__doc__ = f.__doc__
            return decorated
        else:
            raise NotImplementedError
        
    return decorator
