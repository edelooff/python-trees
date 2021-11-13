from __future__ import annotations

from typing import NamedTuple, Optional, Protocol, TypeVar

T = TypeVar("T")
CT = TypeVar("CT", bound="Comparable")
T_NODE = TypeVar("T_NODE", bound="Node")


class Comparable(Protocol):
    def __lt__(self: CT, other: CT) -> bool:
        ...


class Graft(NamedTuple):
    branch: int
    node: Node


class Node(Protocol):
    value: Comparable

    @property
    def left(self: T_NODE) -> Optional[T_NODE]:
        ...

    @property
    def right(self: T_NODE) -> Optional[T_NODE]:
        ...


def unwrap(obj: Optional[T]) -> T:
    """Type checking helper, asserting that the Optional[T] is actually T.

    Raises AssertionError for values that unexpectedly turn out to be None.
    """
    if obj is None:
        raise AssertionError("Unexpected None value")
    return obj
