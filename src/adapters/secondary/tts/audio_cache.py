"""Pequeña caché LRU thread-safe para bytes de audio."""

from collections import OrderedDict
from threading import Lock


class LruAudioCache:
    def __init__(self, max_entries: int) -> None:
        self._max_entries = max_entries
        self._items: OrderedDict[str, bytes] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> bytes | None:
        with self._lock:
            value = self._items.get(key)
            if value is None:
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: bytes) -> None:
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            if len(self._items) > self._max_entries:
                self._items.popitem(last=False)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._items
