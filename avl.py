"""AVL Tree in Python."""


class AVLTree:
    def __init__(self, *initial_values, event_bus=None):
        self.root = None
        if event_bus is None:
            self.publish = lambda topic, **msg: None
        else:
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
        node = self.root
        lineage = [None]
        while node is not None:
            if key < node.value:
                lineage.append(node)
                node = node.left
                continue
            elif key > node.value:
                lineage.append(node)
                node = node.right
                continue

            self.publish("delete", tree=self, node=node)
            if node.balance > 0:
                # Node is right-heavy, find next-larger child node and put its
                # value on the deletion target. Prune the selected node by
                # attaching its children to its parent, and rebalance that.
                *subtree_lineage, closest = ledt_edge_path(node.right)
                lineage.extend(subtree_lineage)
                node.value = closest.value
                if closest is node.right:
                    node.right = closest.right
                    return self.rebalance_removal(node, reversed(lineage), -1)
                closest_parent = lineage.pop()
                closest_parent.left = closest.right
                return self.rebalance_removal(closest_parent, reversed(lineage), 1)
            elif node.left is not None:
                # Node is left-heavy or balanced. Find the next-smaller child
                # node and perform same (mirrored) actions as in previous case.
                *subtree_lineage, closest = right_edge_path(node.left)
                lineage.extend(subtree_lineage)
                node.value = closest.value
                if closest is node.left:
                    node.left = closest.left
                    return self.rebalance_removal(node, reversed(lineage), 1)
                closest_parent = lineage.pop()
                closest_parent.right = closest.left
                return self.rebalance_removal(closest_parent, reversed(lineage), -1)
            parent = lineage.pop()
            if parent is None:
                # Removal of childless root, which requires no rebalancing.
                self.root = None
                return
            elif node is parent.right:
                # Removal of childless leaf node, rebalance from node's parent.
                parent.right = None
                return self.rebalance_removal(parent, reversed(lineage), -1)
            else:
                parent.left = None
                return self.rebalance_removal(parent, reversed(lineage), 1)
        raise KeyError(f"key {key!r} does not exist in tree")

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

    def rebalance_removal(self, node, lineage, balance_change):
        node.balance += balance_change
        for parent in lineage:
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
            if parent is None:
                self.root = subtree_root
            elif node is parent.left:
                parent.left = subtree_root
                parent.balance += 1
            else:
                parent.right = subtree_root
                parent.balance -= 1
            self.publish("balanced", tree=self, root=subtree_root)
            node = parent

    def rotate_left(self, root):
        pivot = root.right
        self.publish("rotate.left", tree=self, nodes={root, pivot})
        root.right = pivot.left
        pivot.left = root
        pivot.balance -= 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_right(self, root):
        pivot = root.left
        self.publish("rotate.right", tree=self, nodes={root, pivot})
        root.left = pivot.right
        pivot.right = root
        pivot.balance += 1
        root.balance = pivot.balance * -1
        return pivot

    def rotate_left_right(self, root):
        smallest = root.left
        pivot = smallest.right
        self.publish("rotate.leftright", tree=self, nodes={root, pivot, smallest})
        smallest.right = pivot.left
        root.left = pivot.right
        pivot.left = smallest
        pivot.right = root
        if pivot.balance < 0:
            root.balance = 1
            smallest.balance = 0
        elif pivot.balance > 0:
            root.balance = 0
            smallest.balance = -1
        else:
            root.balance = 0
            smallest.balance = 0
        pivot.balance = 0
        return pivot

    def rotate_right_left(self, root):
        smallest = root.right
        pivot = smallest.left
        self.publish("rotate.rightleft", tree=self, nodes={root, pivot, smallest})
        smallest.left = pivot.right
        root.right = pivot.left
        pivot.left = root
        pivot.right = smallest
        if pivot.balance < 0:
            root.balance = 0
            smallest.balance = 1
        elif pivot.balance > 0:
            root.balance = -1
            smallest.balance = 0
        else:
            root.balance = 0
            smallest.balance = 0
        pivot.balance = 0
        return pivot


class AVLNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.balance = 0

    def __repr__(self):
        return f"<AVLNode(value={self.value!r})>"


class EventBus:
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


def ledt_edge_path(node):
    """Yields the given node and all children attached on a left edge."""
    while node.left is not None:
        yield node
        node = node.left
    yield node
