#! /usr/bin/python

import dis

def factorial(x, value=1):
	if x == 1:
		return value
	tailcall; factorial(x-1, x*value)

dis.dis(factorial)

