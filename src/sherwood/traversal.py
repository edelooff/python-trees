"""Basic tree traversal algorithms."""

from collections import deque
from typing import Any, Callable, Deque, Iterator, Optional, Union, cast

from .trees.base import Node, Tree

Treelike = Union[Node, Tree]


def breadth_first(tree: Treelike) -> Iterator[Any]:
    """Rank-ordered breadth-first traverser based on a FIFO-queue."""

    def _traverser(node: Node) -> Iterator[Any]:
        nodes = deque([node])
        while nodes:
            node = nodes.popleft()
            yield node.value
            if node.left is not None:
                nodes.append(node.left)
            if node.right is not None:
                nodes.append(node.right)

    return _traverse_tree_or_node(_traverser, tree)


def ordered_iterative(tree: Treelike) -> Iterator[Any]:
    """In-order depth-first-search, implemented as iterative generator."""

    def _traverser(start: Node) -> Iterator[Any]:
        backtracking = False
        parents: Deque[Optional[Node]] = deque([None])
        node: Optional[Node] = start
        while node is not None:
            if not backtracking and node.left is not None:
                parents.append(node)
                node = node.left
                continue
            yield node.value
            if node.right is not None:
                backtracking = False
                node = node.right
                continue
            backtracking = True
            node = parents.pop()

    return _traverse_tree_or_node(_traverser, tree)


def depth_first_inorder(tree: Treelike) -> Iterator[Any]:
    """In-order depth-first-search, implemented as recursive generator."""

    def _in_order_traverser(node: Node) -> Iterator[Any]:
        if node.left is not None:
            yield from _in_order_traverser(node.left)
        yield node.value
        if node.right is not None:
            yield from _in_order_traverser(node.right)

    return _traverse_tree_or_node(_in_order_traverser, tree)


def depth_first_preorder(tree: Treelike) -> Iterator[Any]:
    """Pre-order depth-first-search, implemented as recursive generator."""

    def _pre_order_traverser(node: Node) -> Iterator[Any]:
        yield node.value
        if node.left is not None:
            yield from _pre_order_traverser(node.left)
        if node.right is not None:
            yield from _pre_order_traverser(node.right)

    return _traverse_tree_or_node(_pre_order_traverser, tree)


def depth_first_postorder(tree: Treelike) -> Iterator[Any]:
    """Post-order depth-first-search, implemented as recursive generator."""

    def _post_order_traverser(node: Node) -> Iterator[Any]:
        if node.left is not None:
            yield from _post_order_traverser(node.left)
        if node.right is not None:
            yield from _post_order_traverser(node.right)
        yield node.value

    return _traverse_tree_or_node(_post_order_traverser, tree)


def _traverse_tree_or_node(
    traverser: Callable[[Node], Iterator[Node]], node: Treelike
) -> Iterator[Node]:
    """Applies the traverser to the tree's root, or the given node."""
    if isinstance(node, Tree):
        node = cast(Node, node.root)
    return iter([]) if node is None else traverser(node)
