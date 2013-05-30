import sys
import warnings
from itertools import imap
from types import NoneType

from byteplay import *
hasfunc = set([CALL_FUNCTION, CALL_FUNCTION_VAR, CALL_FUNCTION_KW, CALL_FUNCTION_VAR_KW])
hasexit = set([BREAK_LOOP, CONTINUE_LOOP, RETURN_VALUE, JUMP_FORWARD, POP_JUMP_IF_TRUE, POP_JUMP_IF_FALSE, JUMP_IF_TRUE_OR_POP, JUMP_IF_FALSE_OR_POP, JUMP_ABSOLUTE, FOR_ITER, RAISE_VARARGS])
hasblock = set([SETUP_WITH, SETUP_LOOP, SETUP_EXCEPT, SETUP_FINALLY])
hasendblock = set([POP_BLOCK, END_FINALLY, WITH_CLEANUP])
# YIELD_VALUE isn't really a nonlocal exit, although it does break the dataflow tree

class DataFlowNode(object):
    def __init__(self, op, args, dependencies=(), lineno=None):
        """
        op -> an instance of byeplay.Opcode, the opcode for this node of the tree
        args -> the argument to op, can be anything that byteplay will understand
        dependencies -> a list of (DataFlowNode, int) tuples, the DataFlowNode is bytecode that produced the stack item that this consumed, the int is which of the outputs from the DataFlowNode we consumed
        lineno -> optional, the line number of this opcode
        """
        assert getse(op, args)[0] == len(dependencies), "Wrong number of argument to opcode"
        assert isinstance(op, Opcode)
        # args can be anything
        assert all(map(lambda (x,y): isinstance(x, DataFlowNode) and isinstance(y, (int, long)), dependencies))
        assert isinstance(lineno, (int, long, NoneType))
        self.op = op
        self.args = args
        self.dependencies = dependencies
        self.lineno = lineno

class ControlFlowNode(object):
    def __init__(self, dataflow, blockstack=list()):
        assert isinstance(dataflow, DataFlowNode)
        # TODO: blockstack type
        self.dataflow = dataflow
        self.blockstack = blockstack

class BlockInfo(object):
    def __init__(self, block_type, start_label, end_label):
        assert block_type in ["LOOP", "EXCEPT", "FINALLY", "FUNCTION"]
        assert isinstance(start_label, Label)
        assert isinstance(end_label, Label)
        self.block_type = block_type
        self.start_label = start_label
        self.end_label = end_label

def parse(code_obj):
    assert isinstance(code_obj, Code)
    code_list = code_obj.code
    
    label_to_controlflow = dict()
    exits = dict()
    # control flow trees point in the direction of execution
    # data flow trees point in the direction opposite execution
    def parse_controlflow(start_index, label, blockstack):
        # TODO: create root ControlFlowNode
        # TODO: add labels to all block begins/ends
        for (i, (op, arg)) in imap(lambda i: (i, code_list[i]), xrange(start_index, len(code_list))):
            if op in hasexit \
               or op in hasblock \
               or op in hasendblock:
                dataflow = parse_dataflow(i)
                
            if op in hasexit:
                if op == BREAK_LOOP:
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding loop exit")
                        elif block.type == "LOOP" or block.type == "FINALLY":
                            exit = block.end_label
                            break
                    retval = ControlFlowNode(dataflow, set([exit]), blockstack[:])
                    exits[label] = (exit,)
                    return retval
                elif op == CONTINUE_LOOP:
                    # continue loop is *only* emitted if an active block needs to be triggered
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding loop beginning")
                        elif block.type == "LOOP":
                            exit = block.start_label
                            break
                        elif block.type == "FINALLY":
                            exit = block.end_label
                            break
                    # we ignore arg because it's possible that we're targeting a FINALLY block
                    retval = ControlFlowNode(dataflow, set([exit]), blockstack[:])
                    exits[label] = (exit,)
                    return retval
                elif op == RETURN_VALUE:
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding function beginning")
                        elif block.type == "FUNCTION" or block.type == "FINALLY":
                            exit = block.end_label
                    exits[label] = (exit,)
                    retval = ControlFlowNode(dataflow, set([exit]), blockstack[:])
                    return retval
                elif op == JUMP_FORWARD:
                    pass
                elif op == POP_JUMP_IF_TRUE:
                    pass
                elif op == POP_JUMP_IF_FALSE:
                    pass
                elif op == JUMP_IF_TRUE_OR_POP:
                    pass
                elif op == JUMP_IF_FALSE_OR_POP:
                    pass
                elif op == JUMP_ABSOLUTE:
                    pass
                elif op == FOR_ITER:
                    pass
                elif op == RAISE_VARARGS:
                    pass
                else:
                    raise ValueError("Unrecognized exit opcode")
            elif op in hasblock:
                if op == SETUP_WITH:
                    # see SETUP_FINALLY
                    pass
                elif op == SETUP_LOOP:
                    pass
                elif op == SETUP_EXCEPT:
                    pass
                elif op == SETUP_FINALLY:
                    # targets should be, top of function, containing block, containing loop, and corresponding END_FINALLY
                    pass
                else:
                    raise ValueError("Unrecognized block starting opcode")
            elif op in hasendblock:
                if op == POP_BLOCK:
                    pass
                elif op == END_FINALLY:
                    # see SETUP_FINALLY
                    pass
                elif op == WITH_CLEANUP:
                    # see WITH_CLEANUP
                    pass
                else:
                    raise ValueError("Unrecognized block ending opcode")
            else:
                continue
    
    def parse_dataflow(start_index):
        pass

    
    
    
    
            
def tailcall_optimized(safe=False):
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
            func_args = [None] * (getse(call_opcode, call_args)[0] - 1)
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
                tail_calls.append((tail_call_index, func_index))
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
        for tail_call_index, func_index in potential_tail_calls:
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


        

        return f
        
    return decorator
