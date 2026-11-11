"""Least-recently-used surface storage with a fixed memory budget."""
from collections import OrderedDict


class SurfaceCache:
    def __init__(self, max_bytes):
        self.max_bytes = max_bytes
        self.bytes_used = 0
        self.items = OrderedDict()

    def get(self, key):
        surface = self.items.get(key)
        if surface is not None:
            self.items.move_to_end(key)
        return surface

    def put(self, key, surface):
        old = self.items.pop(key, None)
        if old is not None:
            self.bytes_used -= old.get_pitch()*old.get_height()
        size = surface.get_pitch()*surface.get_height()
        if size > self.max_bytes:
            return
        while self.items and self.bytes_used+size > self.max_bytes:
            _, oldest = self.items.popitem(last=False)
            self.bytes_used -= oldest.get_pitch()*oldest.get_height()
        self.items[key] = surface
        self.bytes_used += size

    def clear(self):
        self.items.clear()
        self.bytes_used = 0
