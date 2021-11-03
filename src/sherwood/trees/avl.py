"""AVL Tree in Python."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, List, Optional, cast, final

from .base import BinaryNode, Branch, Tree
from .utils import left_edge_path, right_edge_path


@final
@dataclass(eq=False)
class AVLNode(BinaryNode):
    balance: int = 0
    left: Optional[AVLNode] = None
    right: Optional[AVLNode] = None


class AVLTree(Tree):
    root: Optional[AVLNode]

    def delete(self, key: Any) -> None:
        """Deletes a key from the AVL tree, or raises if it doesn't exist."""
        lineage = list(self._trace(key))
        node = cast(AVLNode, lineage[-1])
        self.publish("delete", node)
        if node.balance > 0:
            # Node is right-heavy, find next-larger child node and put its
            # value on the deletion target. Prune the selected node by
            # attaching its children to its parent, and rebalance that.
            *subtree, tail = left_edge_path(node.right)
            lineage.extend(subtree)
            node.value = tail.value
            deleted = Branch.right if tail is node.right else Branch.left
            return self.rebalance_removal(lineage, deleted=deleted, new=tail.right)
        elif node.left is not None:
            # Node is left-heavy or balanced. Find the next-smaller child
            # node and perform same (mirrored) actions as in previous case.
            *subtree, tail = right_edge_path(node.left)
            lineage.extend(subtree)
            node.value = tail.value
            deleted = Branch.left if tail is node.left else Branch.right
            return self.rebalance_removal(lineage, deleted=deleted, new=tail.left)
        parent = lineage[-2]
        if parent is None:
            # Removal of childless root, which requires no rebalancing.
            self.root = None
            return
        # Removal of childless leaf node, rebalance from node's parent.
        deleted = Branch.left if node is parent.left else Branch.right
        return self.rebalance_removal(lineage[:-1], deleted=deleted)

    def insert(self, key: Any) -> AVLNode:
        if self.root is None:
            self.root = AVLNode(key)
            self.publish("insert", self.root)
            return self.root

        node = self.root
        lineage = []
        while True:
            lineage.append(node)
            if key == node.value:
                raise ValueError(f"duplicate key {key!r} in AVL Tree")
            elif key < node.value:
                if node.left is not None:
                    node = node.left
                    continue
                node.left = new = AVLNode(key)
            else:
                if node.right is not None:
                    node = node.right
                    continue
                node.right = new = AVLNode(key)
            self.publish("insert", new)
            self.rebalance(new, reversed(lineage))
            return new

    def _trace(self, key: Any) -> Iterator[Optional[AVLNode]]:
        """Traces a path from the root down to the requested key, or raises KeyError."""
        node = self.root
        yield None
        while node is not None:
            yield node
            if key == node.value:
                return
            elif key < node.value:
                node = node.left
            else:
                node = node.right
        raise KeyError(f"key {key!r} does not exist in tree")

    # #########################################################################
    # Tree rebalancing and rotating
    #
    def rebalance(self, node: AVLNode, lineage: Iterator[AVLNode]) -> None:
        for parent in lineage:
            parent.balance += -1 if node is parent.left else 1
            if parent.balance == 0:
                break
            elif parent.balance in {-1, 1}:
                node = parent
                continue
            # Determine rotation necessary to rebalance tree
            elif parent.balance > 1:
                same = node.balance >= 0
                rotate = self.rotate_left if same else self.rotate_right_left
            else:
                same = node.balance <= 0
                rotate = self.rotate_right if same else self.rotate_left_right
            # Attach rebalanced subtree to grandparent, or tree root
            grandparent = next(lineage, None)
            subtree = rotate(parent)
            if grandparent is None:
                self.root = subtree
            elif parent is grandparent.left:
                grandparent.left = subtree
            else:
                grandparent.right = subtree
            self.publish("balanced", subtree, subtree.left, subtree.right)
            break

    def rebalance_removal(
        self,
        lineage: List[Optional[AVLNode]],
        *,
        deleted: Branch,
        new: Optional[AVLNode] = None,
    ) -> None:
        node = cast(AVLNode, lineage.pop())
        if deleted is Branch.left:
            node.balance += 1
            node.left = new
        else:
            node.balance -= 1
            node.right = new
        for parent in reversed(lineage):
            if node.balance == 0 and parent is not None:
                parent.balance += 1 if node is parent.left else -1
                node = parent
                continue
            elif node.balance in {-1, 0, 1}:
                return
            # Determine rotation necessary to rebalance tree
            elif node.balance > 1:
                same = node.right.balance >= 0  # type: ignore[union-attr]
                rotate = self.rotate_left if same else self.rotate_right_left
            else:
                same = node.left.balance <= 0  # type: ignore[union-attr]
                rotate = self.rotate_right if same else self.rotate_left_right
            # Attach rebalanced subtree to grandparent, or tree root
            subtree = rotate(node)
            balance_change = 1 - abs(subtree.balance)
            if parent is None:
                self.root = subtree
            elif node is parent.left:
                parent.left = subtree
                parent.balance += balance_change
            else:
                parent.right = subtree
                parent.balance -= balance_change
            self.publish("balanced", subtree, subtree.left, subtree.right)
            if balance_change == 0:
                break  # Subtree height did not change, rebalancing is done
            node = cast(AVLNode, parent)

    def rotate_left(self, root: AVLNode) -> AVLNode:
        """Hoists the right child to this node's parent position."""
        pivot = cast(AVLNode, root.right)
        self.publish("rotate.left", root, pivot)
        root.right, pivot.left = pivot.left, root
        pivot.balance -= 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_right(self, root: AVLNode) -> AVLNode:
        """Hoists the left child to this node's parent position."""
        pivot = cast(AVLNode, root.left)
        self.publish("rotate.right", root, pivot)
        root.left, pivot.right = pivot.right, root
        pivot.balance += 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_left_right(self, root: AVLNode) -> AVLNode:
        """Hoists the left->right grandchild to this node's parent position."""
        smallest = cast(AVLNode, root.left)
        pivot = cast(AVLNode, smallest.right)
        self.publish("rotate.leftright", root, pivot, smallest)
        smallest.right, root.left = pivot.left, pivot.right
        pivot.left, pivot.right = smallest, root
        root.balance = int(pivot.balance < 0)
        smallest.balance = -int(pivot.balance > 0)
        pivot.balance = 0
        return pivot

    def rotate_right_left(self, root: AVLNode) -> AVLNode:
        """Hoists the right->left grandchild to this node's parent position."""
        largest = cast(AVLNode, root.right)
        pivot = cast(AVLNode, largest.left)
        self.publish("rotate.rightleft", root, pivot, largest)
        root.right, largest.left = pivot.left, pivot.right
        pivot.left, pivot.right = root, largest
        root.balance = -int(pivot.balance > 0)
        largest.balance = int(pivot.balance < 0)
        pivot.balance = 0
        return pivot
