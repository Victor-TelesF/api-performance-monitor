"""Cache LRU de PNGs limitado por bytes e quantidade de entradas, por processo."""

from collections import OrderedDict
from threading import Lock

ChartKey = tuple[str, bytes, int | None, bool]


class PngCache:
    def __init__(self, *, max_bytes: int = 16 * 1024 * 1024, max_entries: int = 64):
        self._max_bytes = max_bytes
        self._max_entries = max_entries
        self._entries: OrderedDict[ChartKey, bytes] = OrderedDict()
        self._size = 0
        self._lock = Lock()

    def get(self, key: ChartKey) -> bytes | None:
        with self._lock:
            value = self._entries.get(key)
            if value is not None:
                self._entries.move_to_end(key)
            return value

    def put(self, key: ChartKey, value: bytes) -> None:
        with self._lock:
            previous = self._entries.pop(key, None)
            if previous is not None:
                self._size -= len(previous)
            if len(value) > self._max_bytes or self._max_entries < 1:
                return
            self._entries[key] = value
            self._size += len(value)
            while self._size > self._max_bytes or len(self._entries) > self._max_entries:
                _, removed = self._entries.popitem(last=False)
                self._size -= len(removed)
