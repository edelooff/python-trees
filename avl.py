"""AVL Tree in Python."""


class AVLTree:
    def __init__(self):
        self.root = None

    def __contains__(self, key):
        node = self.root
        while node is not None:
            if key == node.value:
                return True
            node = node.right if key > node.value else node.left
        return False

    def insert(self, key):
        if self.root is None:
            self.root = AVLNode(key)
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
            self.rebalance(new)
            return new

    # #########################################################################
    # Tree rebalancing and rotating
    #
    def rebalance(self, node):
        while node.parent is not None:
            parent = node.parent
            if node is parent.right:
                if parent.balance > 0:
                    grandparent = parent.parent
                    if node.balance < 0:
                        rebalanced_root = self.rotate_right_left(parent)
                    else:
                        rebalanced_root = self.rotate_left(parent)
                elif parent.balance < 0:
                    parent.balance = 0
                    break
                else:
                    parent.balance += 1
                    node = parent
                    continue
            else:
                if parent.balance < 0:
                    grandparent = parent.parent
                    if node.balance > 0:
                        rebalanced_root = self.rotate_left_right(parent)
                    else:
                        rebalanced_root = self.rotate_right(parent)
                elif parent.balance > 0:
                    parent.balance = 0
                    break
                else:
                    parent.balance -= 1
                    node = parent
                    continue
            rebalanced_root.parent = grandparent
            if grandparent is None:
                self.root = rebalanced_root
            elif parent is grandparent.left:
                grandparent.left = rebalanced_root
            else:
                grandparent.right = rebalanced_root
            break

    def rotate_left(self, root):
        pivot = root.right
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

    def __hash__(self):
        return id(self)

    def assign_left(self, child):
        self.left = child
        if child is not None:
            child.parent = self

    def assign_right(self, child):
        self.right = child
        if child is not None:
            child.parent = self
