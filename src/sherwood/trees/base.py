from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Iterable, Optional

from ..typing import Comparable, Node

if TYPE_CHECKING:
    from ..events import Bus


class Branch(Enum):
    left = auto()
    right = auto()
    __inverted__ = {left: right, right: left}

    @property
    def inverse(self) -> Branch:
        return Branch(self.__inverted__[self.value])


@dataclass
class BinaryNode:
    value: Comparable
    left: Optional[BinaryNode] = None
    right: Optional[BinaryNode] = None

    def __eq__(self, other: Any) -> bool:
        return self is other

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

    @abstractmethod
    def delete(self, key: Any) -> None:
        ...

    @abstractmethod
    def insert(self, key: Any) -> Node:
        ...

    def publish(self, topic: str, *nodes: Optional[Node]) -> None:
        if self.bus is not None:
            if self.root is None:
                raise ValueError("Cannot publish events for empty tree.")
            self.bus.publish(topic, self.root, set(filter(None, nodes)))
