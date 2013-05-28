import sys
import warnings

from decorator import FunctionMaker
def decorator_apply(dec, func):
    """
    Decorate a function by preserving the signature even if dec
    is not a signature-preserving decorator.
    """
    return FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec(func)), __wrapped__=func)

from byteplay import *
hasfunc = set([CALL_FUNCTION, CALL_FUNCTION_VAR, CALL_FUNCTION_KW, CALL_FUNCTION_VAR_KW])

class TailRecursive(object):
    """
    tail_recursive decorator based on Kay Schluehr's recipe
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496691
    with improvements by Michele Simionato and George Sakkis.
    """

    def __init__(self, func):
        self.func = func
        self.firstcall = True
        self.CONTINUE = object() # sentinel

    def __call__(self, *args, **kwd):
        CONTINUE = self.CONTINUE
        if self.firstcall:
            func = self.func
            self.firstcall = False
            try:
                while True:
                    result = func(*args, **kwd)
                    if result is CONTINUE: # update arguments
                        args, kwd = self.argskwd
                    else: # last call
                        return result
            finally:
                self.firstcall = True
        else: # return the arguments of the tail call
            self.argskwd = args, kwd
            return CONTINUE
        
def tailcall_optimized(only_tail_calls=False, safe=False):
    # This probably can't handle functions with >255 arguments
    if sys.version[:5] != "2.7.5":
        warnings.warn("tailcall_optimized was written for python 2.7.5. Behavior may not be correct for other versions")
    def decorator(f):
        assert inspect.isfunction(f)
        c = Code.from_code(f.func_code)


        # Find all tail calls, including non-recursive ones
        potential_tail_calls = list()
        last_instruction = None
        for (i, (instruction, arg)) in enumerate(c.code):
            if last_instruction in hasfunc \
               and instruction == RETURN_VALUE:
                potential_tail_calls.append(i - 1)
            last_instruction = instruction
        # cleanup
        del instruction
        del last_instruction


        # Find all recursive tail calls
        print potential_tail_calls
        tail_calls = list()
        for tail_call_index in potential_tail_calls:
            (call_opcode, call_args) = c.code[tail_call_index]
            func_args_counter = getse(call_opcode, call_args)[0] - 1
            for i in xrange(tail_call_index-1, -1, -1):
                (pops, pushes) = getse(*c.code[i])
                func_args_counter += pops - pushes
                if func_args_counter < 0:
                    raise ValueError("Misaligned function call opcode")
                elif func_args_counter == 0:
                    func_index = i-1
                    break
            if (c.code[func_index] == (LOAD_ATTR, f.func_name) # recursive method call
                and c.code[func_index-1] == (LOAD_FAST, 'self')) \
                or c.code[func_index] == (LOAD_GLOBAL, f.func_name): # ordinary recursion
                print "Found recursion from %s to %s" % (func_index, tail_call_index)
                tail_calls.append(tail_call_index)
            else:
                print "Non-recursive tail call"
            # cleanup
            del call_opcode
            del call_args
            del func_args_counter
            del pops
            del pushes
            try:
                del func_index
            except NameError:
                pass
        del tail_call_index


        # Generate replacement bytecode
        # Yeah, this is duplicated code, but doing things in stages makes
        # the separation of concerns better
        for tail_call_index in potential_tail_calls:
            (call_opcode, call_args) = c.code[tail_call_index]
            num_pos_args = call_args & 0xFF
            num_key_args = (call_args >> 8) & 0xFF
            if call_opcode == CALL_FUNCTION:
                has_var = False
                has_kw = False
            elif call_opcode == CALL_FUNCTION_VAR:
                has_var = True
                has_kw = False
            elif call_opcode == CALL_FUNCTION_KW:
                has_var = False
                has_kw = True
            elif call_opcode == CALL_FUNCTION_VAR_KW:
                has_var = True
                has_kw = True
            else:
                raise ValueError("Unexpected opcode",call_opcode)

            if safe:
                raise NotImplementedError
            else:
                raise NotImplementedError


        

        if only_tail_calls:
            return decorator_apply(TailRecursive, f)
        else:
            return f
        
    return decorator
