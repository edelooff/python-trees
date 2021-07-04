from __future__ import annotations

from typing import Optional, Protocol, TypeVar

CT = TypeVar("CT", bound="Comparable")


class Comparable(Protocol):
    def __lt__(self: CT, other: CT) -> bool:
        ...


class Node(Protocol):
    value: Comparable

    @property
    def left(self) -> Optional[Node]:
        ...

    @property
    def right(self) -> Optional[Node]:
        ...
