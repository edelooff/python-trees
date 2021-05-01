from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class Branch(Enum):
    left = auto()
    right = auto()


@dataclass
class Node:
    value: Any
    left: Optional[Node] = None
    right: Optional[Node] = None

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}(value={self.value!r}) @ {hex(id(self))}>"
