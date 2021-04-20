"""AVL Tree in Python."""

from enum import Enum, auto


class Branch(Enum):
    left = auto()
    right = auto()


class AVLTree:
    def __init__(self, *initial_values, event_bus=None):
        self.root = None
        if event_bus is None:
            self.publish = lambda topic, **msg: None
        else:  # pragma: no cover
            self.publish = event_bus.publish
        self.bulk_insert(*initial_values)

    def __contains__(self, key):
        node = self.root
        while node is not None:
            if key == node.value:
                return True
            node = node.right if key > node.value else node.left
        return False

    def bulk_insert(self, *values):
        """Inserts values from any iterable."""
        if len(values) == 1:
            values = values[0]
        for value in values:
            self.insert(value)

    def delete(self, key):
        """Deletes a key from the AVL tree, or raises if it doesn't exist."""
        lineage = list(self._trace(key))
        node = lineage[-1]
        self.publish("delete", tree=self, node=node)
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

    def insert(self, key):
        if self.root is None:
            self.root = AVLNode(key)
            self.publish("insert", tree=self, node=self.root)
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
            self.publish("insert", tree=self, node=new)
            self.rebalance(new, reversed(lineage))
            return new

    def _trace(self, key):
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
    def rebalance(self, node, lineage):
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
            subtree_root = rotate(parent)
            if grandparent is None:
                self.root = subtree_root
            elif parent is grandparent.left:
                grandparent.left = subtree_root
            else:
                grandparent.right = subtree_root
            self.publish("balanced", tree=self, root=subtree_root)
            break

    def rebalance_removal(self, lineage, *, deleted, new=None):
        node = lineage.pop()
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
                same = node.right.balance >= 0
                rotate = self.rotate_left if same else self.rotate_right_left
            else:
                same = node.left.balance <= 0
                rotate = self.rotate_right if same else self.rotate_left_right
            # Attach rebalanced subtree to grandparent, or tree root
            subtree_root = rotate(node)
            balance_change = 1 - abs(subtree_root.balance)
            if parent is None:
                self.root = subtree_root
            elif node is parent.left:
                parent.left = subtree_root
                parent.balance += balance_change
            else:
                parent.right = subtree_root
                parent.balance -= balance_change
            if balance_change == 0:
                break  # Subtree height did not change, rebalancing is done
            self.publish("balanced", tree=self, root=subtree_root)
            node = parent

    def rotate_left(self, root):
        """Hoists the right child to this node's parent position."""
        pivot = root.right
        self.publish("rotate.left", tree=self, nodes={root, pivot})
        root.right, pivot.left = pivot.left, root
        pivot.balance -= 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_right(self, root):
        """Hoists the left child to this node's parent position."""
        pivot = root.left
        self.publish("rotate.right", tree=self, nodes={root, pivot})
        root.left, pivot.right = pivot.right, root
        pivot.balance += 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_left_right(self, root):
        """Hoists the left->right grandchild to this node's parent position."""
        smallest = root.left
        pivot = smallest.right
        self.publish("rotate.leftright", tree=self, nodes={root, pivot, smallest})
        smallest.right, root.left = pivot.left, pivot.right
        pivot.left, pivot.right = smallest, root
        root.balance = int(pivot.balance < 0)
        smallest.balance = -int(pivot.balance > 0)
        pivot.balance = 0
        return pivot

    def rotate_right_left(self, root):
        """Hoists the right->left grandchild to this node's parent position."""
        largest = root.right
        pivot = largest.left
        self.publish("rotate.rightleft", tree=self, nodes={root, pivot, largest})
        root.right, largest.left = pivot.left, pivot.right
        pivot.left, pivot.right = root, largest
        root.balance = -int(pivot.balance > 0)
        largest.balance = int(pivot.balance < 0)
        pivot.balance = 0
        return pivot


class AVLNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.balance = 0

    def __repr__(self):  # pragma: no cover
        return f"<AVLNode(value={self.value!r})>"


class EventBus:  # pragma: no cover
    """A trivial pub/sub model to allow observation of tree internals."""

    def __init__(self):
        self.subscribers = {}

    def publish(self, topic, **message):
        full_topic = topic
        while topic:
            for handler in self.subscribers.get(topic, ()):
                handler(full_topic, message)
            topic, _, _ = topic.rpartition(".")

    def subscribe(self, topic, handler=None):
        def _wrapper(handler):
            self.subscribers.setdefault(topic, set()).add(handler)
            return handler

        return _wrapper if handler is None else _wrapper(handler)

    def unsubscribe(self, handler):
        for handlers in self.subscribers.values():
            handlers.discard(handler)


def right_edge_path(node):
    """Yields the given node and all children attached on a right edge."""
    while node.right is not None:
        yield node
        node = node.right
    yield node


def left_edge_path(node):
    """Yields the given node and all children attached on a left edge."""
    while node.left is not None:
        yield node
        node = node.left
    yield node
