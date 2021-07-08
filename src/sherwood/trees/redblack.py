from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from itertools import takewhile
from typing import Any, Iterator, Optional, final

from .base import BinaryNode, Tree


class Color(Enum):
    red = auto()
    black = auto()
    __inverted__ = {red: black, black: red}

    @property
    def inverse(self) -> Color:
        return Color(self.__inverted__[self.value])


@final
@dataclass(eq=False)
class RBNode(BinaryNode):
    color: Color = Color.red
    left: Optional[RBNode] = None
    right: Optional[RBNode] = None


class RedBlackTree(Tree):
    root: Optional[RBNode]

    def delete(self, key: Any) -> None:
        raise NotImplementedError

    def insert(self, key: Any) -> RBNode:
        if self.root is None:
            self.root = RBNode(key)
            self.publish("insert", self.root)
            return self.root

        lineage = [node := self.root]
        while True:
            if key == node.value:
                raise ValueError(f"duplicate key {key!r} in Red-Black Tree")
            elif key < node.value:
                if node.left is not None:
                    lineage.append(node := node.left)
                    continue
                node.left = new = RBNode(key)
            else:
                if node.right is not None:
                    lineage.append(node := node.right)
                    continue
                node.right = new = RBNode(key)
            self.publish("insert", new)
            self.rebalance(new, reversed(lineage))
            return new

    def rebalance(self, node: RBNode, lineage: Iterator[RBNode]) -> None:
        """Rebalances the red-black tree after insertion of a new node."""
        # lineage traversal includes the 'parent is black' termination condition
        for parent in takewhile(lambda node: node.color is not Color.black, lineage):
            if parent is self.root:
                parent.color = Color.black
                self.publish("recolor", parent)
                break
            grandparent = next(lineage)
            if has_same_colored_children(grandparent):
                invert_color(grandparent, grandparent.left, grandparent.right)
                node = grandparent
                self.publish("recolor", node, node.left, node.right)
                continue
            # Determine rotation necessary to rebalance tree
            if node is parent.left:
                same = parent is grandparent.left
                rotate = self.rotate_right if same else self.rotate_right_left
            else:
                same = parent is grandparent.right
                rotate = self.rotate_left if same else self.rotate_left_right
            # Attach rebalanced subtree to grandparent, or tree root
            subtree = rotate(grandparent, parent, node)
            if (anchor := next(lineage, None)) is None:
                self.root = subtree
            elif anchor.left is grandparent:
                anchor.left = subtree
            else:
                anchor.right = subtree
            self.publish("balanced", subtree, subtree.left, subtree.right)
            break

    def rotate_left(self, root: RBNode, pivot: RBNode, tail: RBNode) -> RBNode:
        """Hoists the pivot up to to be the new root of the given triple."""
        self.publish("rotate.left", root, pivot, tail)
        root.right, pivot.left = pivot.left, root
        invert_color(root, pivot)
        return pivot

    def rotate_right(self, root: RBNode, pivot: RBNode, tail: RBNode) -> RBNode:
        """Hoists the pivot up to to be the new root of the given triple."""
        self.publish("rotate.right", root, pivot, tail)
        root.left, pivot.right = pivot.right, root
        invert_color(root, pivot)
        return pivot

    def rotate_left_right(self, root: RBNode, outer: RBNode, pivot: RBNode) -> RBNode:
        """Hoists the pivot up to to be the new root of the given triple."""
        self.publish("rotate.leftright", root, pivot, outer)
        outer.right, root.left = pivot.left, pivot.right
        pivot.left, pivot.right = outer, root
        invert_color(root, pivot)
        return pivot

    def rotate_right_left(self, root: RBNode, outer: RBNode, pivot: RBNode) -> RBNode:
        """Hoists the pivot up to to be the new root of the given triple."""
        self.publish("rotate.rightleft", root, pivot, outer)
        root.right, outer.left = pivot.left, pivot.right
        pivot.left, pivot.right = root, outer
        invert_color(root, pivot)
        return pivot


def has_same_colored_children(node: RBNode) -> bool:
    return (
        node.left is not None
        and node.right is not None
        and node.left.color is node.right.color
    )


def invert_color(*nodes: Optional[RBNode]) -> None:
    for node in filter(None, nodes):
        node.color = node.color.inverse
