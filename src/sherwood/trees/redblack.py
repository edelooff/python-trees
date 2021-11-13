from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain, islice, repeat, takewhile, tee
from typing import Any, Iterable, Iterator, Optional, final

from ..typing import unwrap
from .base import BinaryNode, Branch, Tree
from .utils import left_edge_path, right_edge_path


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


@dataclass
class NodeCluster:
    tree: RedBlackTree
    node: RBNode
    parent: RBNode
    grandparent: Optional[RBNode]
    dir: Branch

    @property
    def sibling(self) -> RBNode:
        return getattr(self.parent, self.dir.inverse.name)

    @property
    def close_cousin(self) -> Optional[RBNode]:
        return getattr(self.sibling, self.dir.name)

    @property
    def distant_cousin(self) -> Optional[RBNode]:
        return getattr(self.sibling, self.dir.inverse.name)

    def reattach_rotated(self, subtree: RBNode) -> None:
        if self.grandparent is None:
            self.tree.root = subtree
        else:
            replace_child(self.parent, self.grandparent, subtree)
        self.grandparent = subtree


class RedBlackTree(Tree):
    root: Optional[RBNode]

    def delete(self, key: Any) -> None:
        lineage, lineage_parents = tee(reversed(list(self._trace(key))))
        node = next(lineage_parents)
        self.publish("delete", node)
        if node is self.root and node.left is node.right is None:
            self.root = None
            return  # trivial case 1
        elif node.left is not None and node.right is not None:
            # Find closest relative of two children to limit removal space
            left_children = list(right_edge_path(node.left))
            right_children = list(left_edge_path(node.right))
            child_tree = max(left_children, right_children, key=len)
            lineage, lineage_parents = tee(chain(reversed(child_tree), lineage))
            tail = next(lineage_parents)
            node.value, tail.value = tail.value, node.value
            node = tail

        if node.color is Color.red:
            # Node has no children and is trivially removable
            return replace_child(node, next(lineage_parents), None)
        elif (child := node.left or node.right) is not None:
            # Node has a single (necessarily red) child, which takes this node's place
            child.color = Color.black
            if node is self.root:
                self.root = child
            else:
                replace_child(node, next(lineage_parents), child)
            return self.publish("recolor", child)

        for cluster in self.lineage_iterator(lineage):
            if cluster.node is node:
                # Delete target node from the tree by severing link down from parent
                setattr(cluster.parent, cluster.dir.name, None)
            if (
                is_black(cluster.parent)
                and is_black(cluster.sibling)
                and is_black(cluster.close_cousin)
                and is_black(cluster.distant_cousin)
            ):
                # D1: Everything is black, paint sibling red and restore path lenghts
                cluster.sibling.color = Color.red
                self.publish("recolor", cluster.sibling)
                continue
            elif cluster.sibling.color is Color.red:
                # D3: Sibling is red with (necessarily) black children; rotate
                triplet = cluster.parent, cluster.sibling, cluster.distant_cousin
                if cluster.dir is Branch.left:
                    subtree = self.rotate_left(*triplet)
                else:
                    subtree = self.rotate_right(*triplet)
                cluster.reattach_rotated(subtree)
                self.publish("balanced", subtree, subtree.left, subtree.right)

            if not is_black(cluster.close_cousin):
                # D5: Sibling is now black, close cousin is red, double rotate
                triplet = cluster.parent, cluster.sibling, unwrap(cluster.close_cousin)
                if cluster.dir is Branch.left:
                    subtree = self.rotate_right_left(*triplet)
                else:
                    subtree = self.rotate_left_right(*triplet)
                subtree.color = cluster.parent.color.inverse
                unwrap(subtree.left).color = Color.black
                unwrap(subtree.right).color = Color.black
                cluster.reattach_rotated(subtree)
                return self.publish("balanced", subtree, subtree.left, subtree.right)
            elif not is_black(cluster.distant_cousin):
                # D6: Sibling is now black, distant cousin is red, rotate
                triplet = cluster.parent, cluster.sibling, cluster.distant_cousin
                if cluster.dir is Branch.left:
                    subtree = self.rotate_left(*triplet)
                else:
                    subtree = self.rotate_right(*triplet)
                subtree.color = cluster.parent.color.inverse
                unwrap(subtree.left).color = Color.black
                unwrap(subtree.right).color = Color.black
                cluster.reattach_rotated(subtree)
                return self.publish("balanced", subtree, subtree.left, subtree.right)
            else:
                # D4: Sibling is black, both cousins are black, repaint sibling
                invert_color(cluster.sibling, cluster.parent)
                return self.publish("recolor", cluster.sibling, cluster.parent)

    def lineage_iterator(self, node_path: Iterable[RBNode]) -> Iterator[NodeCluster]:
        nodes, parents, grandparents = tee(node_path, 3)
        opt_grandparents = chain(grandparents, repeat(None))
        next(islice(parents, 1, 1), None)
        next(islice(opt_grandparents, 2, 2), None)
        for node, parent, grandparent in zip(nodes, parents, opt_grandparents):
            if node is parent.left:
                direction = Branch.left
            elif node is parent.right:
                direction = Branch.right
            else:
                raise ValueError(f"Node {node} not a child of {parent}.")
            yield NodeCluster(self, node, parent, grandparent, direction)

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
            if is_black(grandparent.left) is is_black(grandparent.right):
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


def invert_color(*nodes: Optional[RBNode]) -> None:
    """Inverts color of the given nodes after filtering out None values."""
    for node in filter(None, nodes):
        node.color = node.color.inverse


def is_black(node: Optional[RBNode]) -> bool:
    """Whether or not a node is colored black, with NIL nodes considered black."""
    return node is None or node.color is Color.black


def replace_child(child: RBNode, parent: RBNode, replacement: Optional[RBNode]) -> None:
    if parent.left is child:
        parent.left = replacement
    else:
        parent.right = replacement
