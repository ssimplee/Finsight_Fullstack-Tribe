"""In-process LRU cache for vision results (Member 3).

Keyed by image content hash so repeated identical images avoid duplicate
API calls. Values are VisionResult objects; no credentials are ever cached.
"""

from __future__ import annotations

import os
from collections import OrderedDict
from typing import Any

DEFAULT_CACHE_SIZE = 128


class VisionCache:
    """Simple LRU cache bounded by QWEN_CACHE_SIZE (default 128)."""

    def __init__(self, max_size: int | None = None) -> None:
        if max_size is None:
            max_size = int(os.getenv("QWEN_CACHE_SIZE", DEFAULT_CACHE_SIZE))
        self.max_size = max_size
        self._data: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any:
        value = self._data.get(key)
        if value is not None:
            self._data.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self.max_size:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)