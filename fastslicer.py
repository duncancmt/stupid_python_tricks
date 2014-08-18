from numbers import Integral
from itertools import islice
from sys import maxint

from proxy import BetterProxy

class FastSlicer(BetterProxy):
    def __new__(cls, obj, start=None, stop=None, *args, **kwargs):
        return super(FastSlicer, cls).__new__(cls, obj, *args, **kwargs)
    
    def __init__(self, obj, start=None, stop=None):
        super(FastSlicer, self).__init__(obj)
        if isinstance(obj, FastSlicer):
            self._obj = obj._obj
            object.__setattr__(self, 'start', obj.start)
            object.__setattr__(self, 'stop', obj.stop)
            self.start, self.stop = self._get_concrete_index(start, default=0), \
                                    self._get_concrete_index(stop, default=len(self))
        else:
            if start is None:
                start = 0
            if stop is None:
                stop = len(obj)
            if start < 0 or start > len(obj):
                raise IndexError('Invalid start index')
            if stop < 0 or stop > len(obj):
                raise IndexError('Invalid stop index')

            object.__setattr__(self, 'start', start)
            object.__setattr__(self, 'stop', stop)

    def _get_concrete_index(self, index, default=0):
        if index is None:
            index = default
        elif index > len(self):
            index = len(self)
        if index < 0:
            index += self.stop
        else:
            index += self.start
        if index < self.start or index > self.stop:
            raise IndexError('Index outside slice bounds')
        return index

    def __len__(self):
        return self.stop - self.start

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            start = self._get_concrete_index(key.start, default=0)
            stop = self._get_concrete_index(key.stop, default=len(self))
            
            return type(self)(self._obj, start=start, stop=stop)
        elif isinstance(key, Integral):
            key = self._get_concrete_index(key, default=0)
            return self._obj[key]
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __getslice__(self, i, j):
        if i < 0:
            raise IndexError('Starting index out of bounds')
        if j < 0:
            raise IndexError('Ending index out of bounds')
        return self.__getitem__(slice(i,j))
            
    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            start = self._get_concrete_index(key.start, default=0)
            stop = self._get_concrete_index(key.stop, default=len(self))
            if len(value) != stop-start:
                import warnings
                warnings.warn('Changing the length of a FastSlicer instance may have unexpected results')
            self._obj[start:stop] = value
        elif isinstance(key, Integral):
            key = self._get_concrete_index(key, default=0)
            self._obj[key] = value
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __setslice__(self, i, j, seq):
        if i < 0:
            raise IndexError('Starting index out of bounds')
        if j < 0:
            raise IndexError('Ending index out of bounds')
        return self.__setitem__(slice(i,j), seq)

    def __delitem__(self, key):
        import warnings
        warnings.warn('Deleting elements of a FastSlicer instance may have unexpected results')
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            start = self._get_concrete_index(key.start, default=0)
            stop = self._get_concrete_index(key.stop, default=len(self))

            del self._obj[start:stop]
        elif isinstance(key, Integral):
            key = self._get_concrete_index(key, default=0)
            del self._obj[key]
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __delslice__(self, i, j):
        if i < 0:
            raise IndexError('Starting index out of bounds')
        if j < 0:
            raise IndexError('Ending index out of bounds')
        return self.__delitem__(slice(i,j))
        
    def __str__(self):
        return str(self._obj[self.start:self.stop])

    def __iter__(self):
        return islice(self._obj, self.start, self.stop)

    def __bool__(self):
        return len(self) > 0

    # # TODO: implement:
    # def __reversed__(self):
    # def __contains__(self, item):
