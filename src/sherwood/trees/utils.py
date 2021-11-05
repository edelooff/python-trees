from typing import Iterator, Optional

from ..typing import T_NODE


def left_edge_path(node: Optional[T_NODE]) -> Iterator[T_NODE]:
    """Yields the given node and all children attached on a left edge."""
    while node is not None:
        yield node
        node = node.left


def right_edge_path(node: Optional[T_NODE]) -> Iterator[T_NODE]:
    """Yields the given node and all children attached on a right edge."""
    while node is not None:
        yield node
        node = node.right
