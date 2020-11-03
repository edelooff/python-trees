"""Basic tree traversal algorithms."""

from collections import deque


def breadth_first(tree):
    """Rank-ordered breadth-first traverser based on a FIFO-queue."""

    def _traverser(node):
        nodes = deque([node])
        while nodes:
            node = nodes.popleft()
            yield node.value
            if node.left is not None:
                nodes.append(node.left)
            if node.right is not None:
                nodes.append(node.right)

    return _traverse_tree_or_node(_traverser, tree)


def ordered_iterative(tree):
    """In-order depth-first-search, implemented as iterative generator."""

    def _traverser(node):
        backtracking = False
        parents = deque([None])
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


def depth_first_inorder(tree):
    """In-order depth-first-search, implemented as recursive generator."""

    def _in_order_traverser(node):
        if node.left is not None:
            yield from _in_order_traverser(node.left)
        yield node.value
        if node.right is not None:
            yield from _in_order_traverser(node.right)

    return _traverse_tree_or_node(_in_order_traverser, tree)


def depth_first_preorder(tree):
    """Pre-order depth-first-search, implemented as recursive generator."""

    def _pre_order_traverser(node):
        yield node.value
        if node.left is not None:
            yield from _pre_order_traverser(node.left)
        if node.right is not None:
            yield from _pre_order_traverser(node.right)

    return _traverse_tree_or_node(_pre_order_traverser, tree)


def depth_first_postorder(tree):
    """Post-order depth-first-search, implemented as recursive generator."""

    def _post_order_traverser(node):
        if node.left is not None:
            yield from _post_order_traverser(node.left)
        if node.right is not None:
            yield from _post_order_traverser(node.right)
        yield node.value

    return _traverse_tree_or_node(_post_order_traverser, tree)


def _traverse_tree_or_node(traverser, node):
    """Applies the traverser to the tree's root, or the given starting node."""
    if hasattr(node, "root"):
        node = node.root
    return iter([]) if node is None else traverser(node)
