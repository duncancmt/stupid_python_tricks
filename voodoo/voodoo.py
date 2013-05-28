#! /usr/bin/python
"""
Voodoo module: Implements a range of white, to grey, to black magic for Python.

Generally, the Voodoo module is divided into two categories of things:
1) Functions to help optimize code, but hopefully not change its behavior much.
2) Functions to help make difficult-to-express behavior easier to express.

A general concept in voodoo is a voodoo decorator.
These are functions that take functions, and modify their bytecode directly.
Often they will search for references to themselves within the function.
For example, one of the most basic voodoo decorators is yankconstants.
For example:

@yankconstants
def f(x):
	v = 0.0
	for i in x:
		v += i * math.cos(1)
	return v

Clearly, math.cos(1) can be precomputed and stored externally.
Yankconstants will automatically rewrite your loop closer to:

	const = math.cos(1)
	for i in x:
		v += i * const

However, yankconstants is actually one step more aggressive:
The constant will be evaluated once at compile time, and not even in your function at all.

In this case, math.cos is marked as a pure function in Voodoo, and therefore this operation is allowed.
If you wish to mark your own functions as pure, you may declare them with:

@pure # Or voodoo.pure, if you didn't import it locally
def f(x): pass

... or, mark any function by simply calling pure on the function.

There are many other voodoo decorators, such as inlineasm:

@inlineasm
def triangular(n):
	result = 0
	for i in xrange(n):
		inlineasm(\"""
			LOAD_FAST result
			LOAD_FAST i
			BINARY_ADD
			STORE_FAST result
		\""")
	return result

"""

import os, dis, array
from opcode import *

word = lambda index : chr(index & 0xff) + chr((index >> 8) & 0xff)

def assemble(code, constants, local, labels, relocations, offset=0): #, local):
	local = dict(list(zip(local, range(len(local)))))
	while "  " in code:
		code = code.replace("  ", " ")
	code = [i for i in (j.split("#")[0].strip() for j in code.split("\n")) if i]
	output = ""
	for line in code:
		op, args = (lambda x : (x[0], x[1:]))(line.split(" "))
		if op[-1] == ":" and len(args) == 0:
			labels[op[:-1]] = len(output) + offset
			continue
		if op not in opmap:
			raise ValueError("Unknown opcode:", op)
		v = opmap[op]
		output += chr(v)
		if v > HAVE_ARGUMENT:
			if v in haslocal:
				index = local[args[0]]
				output += word(index)
			elif v in hasconst:
				value = eval(" ".join(args))
				output += word(len(constants))
				constants.append(value)
			elif v in hasjabs:
				value = args[0]
				relocations.append( (len(output) + offset, value, "abs") )
				output += word(0)
			elif v in hasjrel:
				value = args[0]
				relocations.append( (len(output) + offset, value, "rel") )
				output += word(0)
			else:
				index = eval(" ".join(args))
				output += word(index)

	#def f():
	#	pass
	#f.func_code = type(f.func_code)(0, 0, 10, 0, output, tuple(constants), tuple(local), (), "Assembled", "Sheep", 0, "")
	#return f
	#return output, tuple(constants)
	return output

def relocate(code, labels, relocations):
	code = array.array("b", code)
	for target, value, typ in relocations:
		destination = labels[value]
		if typ == "rel":
			destination -= target+2
		code[target]   = (destination)      & 0xff
		code[target+1] = (destination >> 8) & 0xff
	return code.tostring()

def inlineasm(f):
	"""inlineasm is a Voodoo decorator. (For general information on these, see the voodoo module's docstring.)

	inlineasm(string) -> Assembles string, and directly inserts it into the bytecode stream.
	"""

	if type(f) == str:
		raise ValueError("you may only pass constant strings to inlineasm")
	indexes = [i[0] for i in enumerate(f.func_code.co_names) if i[1] == "inlineasm"]
	if not indexes:
		return f
	assert len(indexes) == 1
	code = f.func_code.co_code
	constants = list(f.func_code.co_consts)
	local = list(f.func_code.co_varnames)
	labels, relocations = {}, []
	new_code = ""
	for i in indexes:
		k, p, l = "t%sd" % (word(i)), 0, 0
		while p >= 0:
			p = code.find(k, p)
			if p != -1:
				if code[p+6:p+10] == "\x83\x01\x00\x01":
					new_code += code[l:p]
					const_index = ord(code[p+4]) + (ord(code[p+5])<<8)
					const = f.func_code.co_consts[const_index]
					new = assemble( const, constants, local, labels, relocations, len(new_code) )
					new_code += new
					p += 10
					l = p
				else:
					p += 1
	new_code += code[l:]
	new_code = relocate( new_code, labels, relocations )
	f.func_code = type(f.func_code)(f.func_code.co_argcount, f.func_code.co_nlocals, f.func_code.co_stacksize+20, 0, new_code, tuple(constants), f.func_code.co_names, tuple(local), f.func_code.co_filename, f.func_code.co_name, f.func_code.co_firstlineno, "")
	return f

