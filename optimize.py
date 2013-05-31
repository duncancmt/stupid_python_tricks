import sys
import warnings
from itertools import imap
from types import NoneType

from byteplay import *
hasfunc = set([CALL_FUNCTION, CALL_FUNCTION_VAR, CALL_FUNCTION_KW, CALL_FUNCTION_VAR_KW])

# These are subtly different from byteplay.hasflow. hasflow includes STOP_CODE (which is ignored by the interpreter) and excludes RAISE_VARARGS (which most definitely effects the control flow).
hasexit = set([BREAK_LOOP, CONTINUE_LOOP, RETURN_VALUE, JUMP_FORWARD, JUMP_ABSOLUTE, POP_JUMP_IF_TRUE, POP_JUMP_IF_FALSE, JUMP_IF_TRUE_OR_POP, JUMP_IF_FALSE_OR_POP, FOR_ITER, RAISE_VARARGS])
hasblock = set([SETUP_WITH, SETUP_LOOP, SETUP_EXCEPT, SETUP_FINALLY])
hasendblock = set([POP_BLOCK, END_FINALLY, WITH_CLEANUP])
# YIELD_VALUE isn't really a nonlocal exit, although it does break the dataflow tree

class DataFlowNode(object):
    def __init__(self, op, args, dependencies=(), lineno=None):
        """
        op -> an instance of byeplay.Opcode, the opcode for this node of the tree
        args -> the argument to op, can be anything that byteplay will understand
        dependencies -> a list of {(DataFlowNode, int) tuple, None}, the DataFlowNode is bytecode that produced the stack item that this consumed, the int is which of the outputs from the DataFlowNode we consumed (a negative value indicates that this node consumes no outputs). None indicates that this dependency lies outside the current ControlFlowNode.
        lineno -> optional, the line number of this opcode
        """
        assert getse(op, args)[0] == len(dependencies), "Wrong number of argument to opcode"
        assert isinstance(op, Opcode)
        # args can be anything
        assert all(map(lambda (x,y): isinstance(x, (DataFlowNode, NoneType)) and isinstance(y, (int, long)), dependencies))
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

def find_offset(code_list, label):
    for (i, (op, arg)) in enumerate(code_list):
        if op == label:
            return i
    raise AttributeError("Label not found")

def parse(code_obj):
    assert isinstance(code_obj, Code)
    # TODO: add labels to all block begins/ends (and only to block begins/ends)
    code_list = code_obj.code
    
    label_to_controlflow = dict()
    exits = dict()
    # control flow trees point in the direction of execution
    # data flow trees point in the direction opposite execution
    def parse_controlflow(start_index, label, blockstack):
        # WARNING: there are always implicit exits from any ControlFlowNode, namely those that raise exceptions.
        #          These are not expressed in the control flow graph, only explicit transfers of control are.
        #          The exception to this rule is FINALLY blocks. These always have edges to all possible exits.
        # TODO: fix and remove above warning
        # TODO: create root ControlFlowNode
        # TODO: appropriately skip over labels when recursing
        # TODO: handle linenumbers
        for (i, (op, arg)) in imap(lambda i: (i, code_list[i]), xrange(start_index, len(code_list))):
            if op in hasexit \
               or op in hasblock \
               or op in hasendblock:
                dataflow = parse_dataflow(i, start_index)
                label_to_controlflow[label] = ControlFlowNode(dataflow, blockstack[:])
            if op in hasexit:
                if op == BREAK_LOOP:
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding loop exit")
                        elif block.type == "LOOP" or block.type == "FINALLY":
                            exit = block.end_label
                            break
                    exits[label] = (exit,)
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
                    exits[label] = (exit,)
                elif op == RETURN_VALUE:
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding function beginning")
                        elif block.type == "FUNCTION" or block.type == "FINALLY":
                            exit = block.end_label
                    exits[label] = (exit,)

                # For all explicitly targeted jumps, we don't verify that the target is valid
                # because we won't be able to serialize invalid targets anyway
                # (an invalid target is one that isn't in the same block scope)
                elif op == JUMP_FORWARD or op == JUMP_ABSOLUTE:
                    # unconditional jumps have only one exit
                    assert isinstance(arg, Label)
                    exits[label] = (arg,)
                    if arg not in exits:
                        parse_controlflow(find_offset(code_list, arg), arg, blockstack[:])

                # conditional jumps have two exits
                elif op == POP_JUMP_IF_TRUE or op == POP_JUMP_IF_FALSE \
                     or op == JUMP_IF_TRUE_OR_POP or op == JUMP_IF_FALSE_OR_POP \
                     or op == FOR_ITER:
                    assert isinstance(arg, Label)
                    next = code_list[i+1][0]
                    assert isinstance(next, Label)
                    exits[label] = (arg,next)
                    if arg not in exits:
                        parse_controlflow(find_offset(code_list, arg), arg, blockstack[:])
                    if next not in exits:
                        parse_controlflow(find_offset(code_list, next), next, blockstack[:])
                elif op == RAISE_VARARGS:
                    for block in blockstack+[None]:
                        if block is None:
                            raise ValueError("Ran out of blocks before finding an exception handler or function beginning")
                        elif block.type in ["EXCEPT", "FINALLY", "FUNCTION"]:
                            exit = block.end_label
                    exits[label] = (exit,)
                else:
                    raise ValueError("Unrecognized exit opcode")
            elif op in hasblock:
                assert isinstance(arg, Label)
                if op == SETUP_WITH:
                    blockinfo = BlockInfo("FINALLY", label, arg)
                elif op == SETUP_LOOP:
                    blockinfo = BlockInfo("LOOP", label, arg)
                elif op == SETUP_EXCEPT:
                    blockinfo = BlockInfo("EXCEPT", label, arg)
                elif op == SETUP_FINALLY:
                    blockinfo = BlockInfo("FINALLY", label, arg)
                else:
                    raise ValueError("Unrecognized block starting opcode")
                exit = code_list[i+1][0]
                assert isinstance(exit, Label)
                exits[label] = (exit,)
                assert exit not in exits
                parse_controlflow(i+1, exit, blockstack+[blockinfo])
            elif op in hasendblock:
                if op == POP_BLOCK:
                    exit = code_list[i+1][0]
                    assert isinstance(exit, Label)
                    exits[label] = (exit,)
                    if exit not in exits:
                        parse_controlflow(i+1, exit, blockstack[:-1])
                elif op == END_FINALLY:
                    # targets should be, bottom of function, containing block's target, containing loop (top and bottom), and falling off the end
                    raise NotImplementedError
                elif op == WITH_CLEANUP:
                    # see END_FINALLY
                    raise NotImplementedError
                else:
                    raise ValueError("Unrecognized block ending opcode")
            elif isinstance(op, Label):
                exits[label] = (op,)
                if exit not in exits:
                    parse_controlflow(i+1, op, blockstack[:])
            elif op == SetLineno:
                # TODO: handle line numbers
                continue
            else:
                continue
        assert all(map(lambda x: x in exits, exits[label])), "Unresolved exit"
    
    def parse_dataflow(exit_index, enter_index):
        def inner(start_index):
            if start_index == enter_index:
                yield (start_index, None)
            elif start_index < enter_index:
                raise ValueError("Ran past the end of the control flow node")
            else:
                (op, arg) = code_list[start_index]
                if op is SetLineno:
                    yield (start_index+1, arg)
                else:
                    (pops, pushes) = getse(op, arg)
                    if pops == 0:
                        node = DataFlowNode(op, arg, (), lineno=None) # TODO: lineno
                    else:
                        dependencies = [None]*pops
                        dependency_index = 0
                        while dependency_index < pops:
                            for (start_index, dependency) in inner(start_index):
                                if isinstance(dependency, (int, long)):
                                    # This is a line number
                                    continue
                                # dependency is either a (node, index) tuple or None (indicating out of range dependency)
                                dependencies[dependency_index] = dependency
                                dependency_index += 1
                        dependencies = tuple(dependencies)
                        node = DataFlowNode(op, arg, dependencies, lineno=None) # TODO: lineno
                    for i in xrange(pushes):
                        yield (start_index+1, (node, i))

        for i in (i, (op, arg)) in imap(lambda i: (i, code_list[i]), xrange(start_index, end_index-1, -1)):
            raise NotImplementedError

    
    
    
    
            
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
