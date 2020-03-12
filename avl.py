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
        while node is not None:
            if key < node.value:
                node = node.left
                continue
            elif key > node.value:
                node = node.right
                continue

            parent = node.parent
            if node.balance > 0:
                # Node is right-heavy, find next-larger child node and put its
                # value on the deletion target. Prune the selected node by
                # attaching its children to its parent, and rebalance that.
                closest = subtree_min(node.right)
                node.value = closest.value
                if closest is node.right:
                    node.assign_right(closest.right)
                    return self.rebalance_removal(node, -1)
                closest.parent.assign_left(closest.right)
                return self.rebalance_removal(closest.parent, 1)
            elif node.left is not None:
                # Node is left-heavy or balanced. Find the next-smaller child
                # node and perform same (mirrored) actions as in previous case.
                closest = subtree_max(node.left)
                node.value = closest.value
                if closest is node.left:
                    node.assign_left(closest.left)
                    return self.rebalance_removal(node, 1)
                closest.parent.assign_right(closest.left)
                return self.rebalance_removal(closest.parent, -1)
            elif parent is None:
                # Removal of childless root, which requires no rebalancing.
                self.root = None
                return
            elif node is parent.right:
                # Removal of childless leaf node, rebalance from node's parent.
                parent.right = None
                return self.rebalance_removal(parent, -1)
            else:
                parent.left = None
                return self.rebalance_removal(parent, 1)
        raise KeyError('key {} does not exist in tree'.format(key))

    def insert(self, key):
        if self.root is None:
            self.root = AVLNode(key)
            self.publish('insert', tree=self, node=self.root)
            return self.root

        node = self.root
        while True:
            if key == node.value:
                raise ValueError('duplicate key in AVL Tree')
            elif key < node.value:
                if node.left is not None:
                    node = node.left
                    continue
                node.left = new = AVLNode(key, parent=node)
            else:
                if node.right is not None:
                    node = node.right
                    continue
                node.right = new = AVLNode(key, parent=node)
            self.publish('insert', tree=self, node=new)
            self.rebalance(new)
            return new

    # #########################################################################
    # Tree rebalancing and rotating
    #
    def rebalance(self, node):
        while node.parent is not None:
            parent = node.parent
            parent.balance += (-1 if node is parent.left else 1)
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
            grandparent = parent.parent
            subtree_root = rotate(parent)
            if grandparent is None:
                self.root = subtree_root
                self.root.parent = None
            elif parent is grandparent.left:
                grandparent.assign_left(subtree_root)
            else:
                grandparent.assign_right(subtree_root)
            self.publish('balanced', tree=self, root=subtree_root)
            break

    def rebalance_removal(self, node, balance_change):
        node.balance += balance_change
        while node is not None:
            parent = node.parent
            if node.balance == 0 and parent is not None:
                parent.balance += 1 if node is parent.left else -1
                node = parent
                continue
            elif node.balance in {-1, 0, 1}:
                return
            # Determine rotation necessary to rebalance tree
            elif node.balance > 1:
                subtree_root = self.rotate_left(node)
            else:
                subtree_root = self.rotate_right(node)
            # Attach rebalanced subtree to grandparent, or tree root
            if parent is None:
                self.root = subtree_root
                self.root.parent = None
            elif node is parent.left:
                parent.assign_left(subtree_root)
                parent.balance += 1
            else:
                parent.assign_right(subtree_root)
                parent.balance -= 1
            self.publish('balanced', tree=self, root=subtree_root)
            node = parent

    def rotate_left(self, root):
        pivot = root.right
        self.publish('rotate.left', tree=self, nodes={root, pivot})
        root.assign_right(pivot.left)
        pivot.assign_left(root)
        if pivot.balance == 0:
            root.balance = 1
            pivot.balance = -1
        else:
            root.balance = 0
            pivot.balance = 0
        return pivot

    def rotate_right(self, root):
        pivot = root.left
        self.publish('rotate.right', tree=self, nodes={root, pivot})
        root.assign_left(pivot.right)
        pivot.assign_right(root)
        if pivot.balance == 0:
            root.balance = -1
            pivot.balance = 1
        else:
            root.balance = 0
            pivot.balance = 0
        return pivot

    def rotate_left_right(self, root):
        smallest = root.left
        pivot = smallest.right
        self.publish('rotate.leftright', tree=self, nodes={
            root, pivot, smallest})
        smallest.assign_right(pivot.left)
        root.assign_left(pivot.right)
        pivot.assign_left(smallest)
        pivot.assign_right(root)
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
        self.publish('rotate.rightleft', tree=self, nodes={
            root, pivot, smallest})
        smallest.assign_left(pivot.right)
        root.assign_right(pivot.left)
        pivot.assign_left(root)
        pivot.assign_right(smallest)
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
    def __init__(self, value, parent=None):
        self.value = value
        self.parent = parent
        self.left = None
        self.right = None
        self.balance = 0

    def __repr__(self):
        return f'<AVLNode(value={self.value!r})>'

    def assign_left(self, child):
        self.left = child
        if child is not None:
            child.parent = self

    def assign_right(self, child):
        self.right = child
        if child is not None:
            child.parent = self


class EventBus:
    """A trivial pub/sub model to allow observation of tree internals."""
    def __init__(self):
        self.subscribers = {}

    def publish(self, topic, **message):
        full_topic = topic
        while topic:
            for handler in self.subscribers.get(topic, ()):
                handler(full_topic, message)
            topic, _, _ = topic.rpartition('.')

    def subscribe(self, topic, handler=None):
        def _wrapper(handler):
            self.subscribers.setdefault(topic, set()).add(handler)
            return handler
        return _wrapper if handler is None else _wrapper(handler)

    def unsubscribe(self, handler):
        for handlers in self.subscribers.values():
            handlers.discard(handler)


def subtree_max(node):
    """Returns the rightmost node in the subtree anchored at node."""
    while node.right is not None:
        node = node.right
    return node


def subtree_min(node):
    """Returns the leftmost node in the subtree anchored at node."""
    while node.left is not None:
        node = node.left
    return node
