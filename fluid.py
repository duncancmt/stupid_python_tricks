# This file is part of stupid_python_tricks written by Duncan Townsend.
#
# stupid_python_tricks is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# stupid_python_tricks is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with stupid_python_tricks.  If not, see <http://www.gnu.org/licenses/>.

import sys
from collections import MutableMapping

from localdata import LocalDict
from immutable import ImmutableDict

def frames_from(frame):
    while frame is not None:
        yield frame
        frame = frame.f_back

class FluidManager(MutableMapping):
    """A class implementing dynamic variables (also called fluids). These
    variables' values are *dynamically* scoped. Each stack has its own
    storage. Bindings (including unbinding) are local to the current stack frame
    and are only visible to those frames "below" that frame i.e. those scopes
    that are created by function calls originating from the current scope. When
    returning from the scope in which a binding was made, the binding is
    transparently undone and restored to its previous value. Each FluidManager
    instances implements its own, distinct name space.

    Usage:
    On initialization, pass FluidManager the initial values that you wish for
    variables it manages to take. These arguments are in the same form as the
    arguments to dict(). To access those variables, you may use dictionary-style
    references (foo[bar]; foo[bar] = baz; del foo[bar]) or attribute-style
    references (foo.bar; foo.bar = baz; del foo.bar). Both styles will access
    the same namespace.
    """

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_frames", LocalDict())
        object.__setattr__(self, "_initial_values", ImmutableDict(*args, **kwargs))
        object.__setattr__(self, "_deletion_sentinel", object())

    def __getattr__(self, name):
        frame = sys._getframe().f_back
        try:
            return self._get_with_frame(name, frame)
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        frame = sys._getframe().f_back
        return self._set_with_frame(name, value, frame)
    def __delattr__(self, name):
        frame = sys._getframe().f_back
        try:
            return self._delete_with_frame(name, frame)
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        frame = sys._getframe().f_back
        return self._get_with_frame(key, frame)
    def __setitem__(self, key, value):
        frame = sys._getframe().f_back
        return self._set_with_frame(key, value, frame)
    def __delitem__(self, key):
        frame = sys._getframe().f_back
        return self._delete_with_frame(key, frame)

    def _cleanup_frames(self, frame):
        active_frames = frozenset(frames_from(frame))
        dead_frames = set()
        for frame in self._frames.iterkeys():
            if frame not in active_frames:
                dead_frames.add(frame)
        for frame in dead_frames:
            del self._frames[frame]
    def _get_with_frame(self, key, frame):
        self._cleanup_frames(frame)
        dummy = {}
        for f in frames_from(frame):
            try:
                ret = self._frames.get(f, dummy)[key]
            except KeyError:
                continue
            if ret is self._deletion_sentinel:
                raise KeyError(key)
            else:
                return ret
        return self._initial_values[key]
    def _set_with_frame(self, key, value, frame):
        self._cleanup_frames(frame)
        self._frames.setdefault(frame, {})[key] = value
    def _delete_with_frame(self, key, frame):
        self._cleanup_frames(frame)
        self._get_with_frame(key, frame) # throws KeyError if key is not present
        self._frames.setdefault(frame, {})[key] = self._deletion_sentinel

    def to_dict(self):
        ret = dict()
        for frame in reversed(list(frames_from(sys._getframe().f_back))):
            try:
                ret.update(self._frames[frame])
            except KeyError:
                continue
        deleted_keys = set()
        for k, v in ret.iteritems():
            if v is self._deletion_sentinel:
                deleted_keys.add(k)
        for k in deleted_keys:
            del ret[k]
        return ret

    def __len__(self):
        return len(self.to_dict())
    def __iter__(self):
        return iter(self.to_dict())
        
__all__ = ["FluidManager"]
