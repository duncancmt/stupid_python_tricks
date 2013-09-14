from collections import deque
from proxy import BetterProxy

class IterWrapper(Wrapper):
    """This class adds a bunch of useful functionality to iterators.

    Subscript notation [] "peeks" ahead in the iterator. If you "peek" a value, it will still be returned by the ".next()" method as usual. If the iterator has terminated before reaching the value you want to "peek", the subscript operation will raise an IndexError.
    
    The "drop" method immediately advances the iterator the given number of items forward, ignoring the values returned. Attempting to drop 0 items does nothing. Attempting to drop more items than the iterator has will raise an IndexError.

    The "push" method adds an arbitrary value to the beginning of the iterator. That is, the next value peeked or returned by ".next()" will be the value supplied to the "push" method.
    It is possible to use the push method to "restart" a finished iterator. If the underlying iterator has previously raised a StopIteration exception, pushing a new value onto the iterator will cause the next invocation of the ".next()" method to return the pushed item.

    All other methods of the iterator are mirrored unmodified.
    """
    def __init__(self, obj):
        try:
            obj.next
        except AttributeError:
            obj = iter(obj)
        super(IterWrapper, self).__init__(obj)
        object.__setattr__(self, '_cache', deque())

    def __iter__(self):
        return self

    def next(self):
        if len(self._cache) == 0:
            return self._obj.next()
        else:
            return self._cache.popleft()

    def drop(self,count):
        if count == 0:
            return
        self[count-1] # ensure we have at least this many 
        for i in xrange(count):
            self._cache.popleft()

    def push(self,item):
        self._cache.appendleft(item)

    def __getitem__(self,index):
        if isinstance(index,slice):
            start, stop, step = index.start, index.stop, index.step

            if start is None:
                start = 0
            elif start < 0:
                raise IndexError("Can't peek from the end of the iterator")
                
            if step is None:
                step = 1
            elif step < 0:
                raise IndexError("Can't peek from the end of the iterator")
                
            if stop is None:
                self._cache.extend(self._obj)
                return list(self._cache[start::step])
            elif stop < 0:
                raise IndexError("Can't peek from the end of the iterator")
            else:
                try:
                    for i in xrange(len(self._cache),stop):
                        self._cache.append(self._obj.next())
                except StopIteration:
                    pass
                return list(self._cache[start:stop:step])
        else:
            if index < 0:
                raise IndexError("Can't peek from the end of the iterator")
            else:
                if len(self._cache) > index:
                    return self._cache[index]
                else:
                    try:
                        for i in xrange(index+1-len(self._cache)):
                            self._cache.append(self._obj.next())
                        return self._cache[index]
                    except StopIteration:
                        raise IndexError("Peek index out of range")
