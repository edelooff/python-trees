from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Iterable, Optional

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

    def __init__(
        self,
        initial_values: Optional[Iterable[Any]] = None,
        /,
        *,
        event_bus: Optional[Bus] = None,
    ):
        self.bus = event_bus
        self.root = None
        if initial_values is not None:
            for value in initial_values:
                self.insert(value)

    def __contains__(self, key: Any) -> bool:
        node = self.root
        while node is not None:
            if key == node.value:
                return True
            node = node.right if key > node.value else node.left
        return False

    def publish(self, name: str, event: Event) -> None:
        if self.bus is not None:
            self.bus.publish(name, event)
