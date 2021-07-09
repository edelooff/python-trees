from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain, takewhile, tee
from typing import Any, Iterable, Iterator, Optional, final

from .base import BinaryNode, Branch, Tree


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


@dataclass(frozen=True)
class NodeRelations:
    node: RBNode
    parent: RBNode
    dir: Branch

    @property
    def sibling(self):
        return getattr(self.parent, self.dir.inverse.name)

    @property
    def close_cousin(self) -> Optional[RBNode]:
        return getattr(self.sibling, self.dir.name)

    @property
    def distant_cousin(self) -> Optional[RBNode]:
        return getattr(self.sibling, self.dir.inverse.name)

    @classmethod
    def from_node_parent(
        cls, node: RBNode, parent: RBNode, direction=Branch
    ) -> NodeRelations:
        if node is parent.left:
            direction = Branch.left
        elif node is parent.right:
            direction = Branch.right
        return cls(node=node, parent=parent, dir=direction)


class RedBlackTree(Tree):
    root: Optional[RBNode]

    def delete(self, key: Any) -> None:
        lineage, lineage_copy = tee(reversed(list(self._trace(key))))
        node = next(lineage_copy)
        self.publish("delete", node)
        if node.left is node.right is None and node is self.root:
            self.root = None
            self.publish("balanced")
            return  # trivial case 1
        elif node.left is not None and node.right is not None:
            # Find closest relative of two children to limit removal space
            left_children = list(right_edge_path(node.left))
            right_children = list(left_edge_path(node.right))
            *child_tree, tail = max(left_children, right_children, key=len)
            node.value = tail.value
            node = tail
            lineage = chain(reversed(child_tree), lineage_copy)

        if node.color is Color.red:
            # Node has no children and is trivially removable
            replace_black_or_prune(node, (target := next(lineage_copy)))
            return self.publish("recolor", target)
        elif (child := node.left or node.right) is not None:
            # Node has a single (necessarily red) child, which takes this node's place
            if node is self.root:
                child.color = Color.black
                self.root = child
            else:
                replace_black_or_prune(node, next(lineage_copy), replacement=child)
            return self.publish("recolor", child)

        parent = next(lineage_copy)
        if node is parent.left:
            branch = Branch.left
            parent.left = None
        else:
            branch = Branch.right
            parent.right = None

        for relation in self.lineage_iterator(lineage, direction=branch):
            if relation.parent is None:
                # D2: We've arrived at the root, all work is done
                return
            elif (
                is_black(relation.parent)
                and is_black(relation.sibling)
                and is_black(relation.close_cousin)
                and is_black(relation.distant_cousin)
            ):
                # D1: Everything is black, paint sibling red and restore path lenghts
                relation.sibling.color = Color.red
                self.publish("recolor", relation.sibling)
                continue
            elif relation.sibling.color is Color.red:
                # D3: Sibling is red with (necessarily) black children; rotate
                is_left = relation.dir is Branch.left
                rotate = self.rotate_left if is_left else self.rotate_right
                subtree = rotate(
                    relation.parent, relation.sibling, relation.distant_cousin
                )
                if relation.parent is self.root:
                    self.root = subtree
                self.publish("balanced", subtree, subtree.left, subtree.right)

            if not is_black(relation.close_cousin):
                # D5
                return
            elif not is_black(relation.distant_cousin):
                # D6
                return
            else:
                # D4: Sibling is black, both cousins are black, repaint sibling
                invert_color(relation.sibling, relation.parent)
                self.publish("recolor", relation.sibling, relation.parent)
                return

    def lineage_iterator(
        self, node_path: Iterable[RBNode], direction=Branch
    ) -> Iterator[NodeRelations]:
        nodes, parents = tee(node_path)
        next(parents, None)
        for node, parent in zip(nodes, parents):
            yield NodeRelations.from_node_parent(node, parent, direction=direction)

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

    def _trace(self, key: Any) -> Iterator[RBNode]:
        """Traces a path from the root down to the requested key, or raises KeyError."""
        node = self.root
        # yield None
        while node is not None:
            yield node
            if key == node.value:
                return
            elif key < node.value:
                node = node.left
            else:
                node = node.right
        raise KeyError(f"key {key!r} does not exist in tree")

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

    def rotate_left(
        self, root: RBNode, pivot: RBNode, tail: Optional[RBNode]
    ) -> RBNode:
        """Hoists the pivot up to to be the new root of the given triple."""
        self.publish("rotate.left", root, pivot, tail)
        root.right, pivot.left = pivot.left, root
        invert_color(root, pivot)
        return pivot

    def rotate_right(
        self, root: RBNode, pivot: RBNode, tail: Optional[RBNode]
    ) -> RBNode:
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


def is_black(node: Optional[RBNode]) -> bool:
    """Whether or not a node is colored black, with NIL nodes considered black."""
    return node is None or node.color is Color.black


def replace_black_or_prune(
    node: RBNode, parent: RBNode, replacement: Optional[RBNode] = None
) -> None:
    if replacement is not None:
        replacement.color = Color.black
    if parent.left is node:
        parent.left = replacement
    else:
        parent.right = replacement


def has_same_colored_children(node: RBNode) -> bool:
    return (
        node.left is not None
        and node.right is not None
        and node.left.color is node.right.color
    )


def invert_color(*nodes: Optional[RBNode]) -> None:
    for node in filter(None, nodes):
        node.color = node.color.inverse


def left_edge_path(node: RBNode) -> Iterator[RBNode]:
    """Yields the given node and all children attached on a left edge."""
    while node.left is not None:
        yield node
        node = node.left
    yield node


def right_edge_path(node: RBNode) -> Iterator[RBNode]:
    """Yields the given node and all children attached on a right edge."""
    while node.right is not None:
        yield node
        node = node.right
    yield node
