from __future__ import annotations

from typing import Optional, Protocol, TypeVar

CT = TypeVar("CT", bound="Comparable")
T_NODE = TypeVar("T_NODE", bound="Node")


class Comparable(Protocol):
    def __lt__(self: CT, other: CT) -> bool:
        ...


class Node(Protocol):
    value: Comparable

    @property
    def left(self: T_NODE) -> Optional[T_NODE]:
        ...

    @property
    def right(self: T_NODE) -> Optional[T_NODE]:
        ...
