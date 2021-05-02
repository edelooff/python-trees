from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..events import Bus, Event


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


class Tree(ABC):
    bus: Optional[Bus]
    root: Optional[Node]

    def __init__(self, *initial_values: Any, event_bus: Optional[Bus] = None):
        self.bus = event_bus
        self.root = None
        self.bulk_insert(*initial_values)

    @abstractmethod
    def bulk_insert(self, *values: Any) -> None:
        ...

    def publish(self, name: str, event: Event) -> None:
        if self.bus is not None:
            self.bus.publish(name, event)
