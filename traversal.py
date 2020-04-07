"""Basic tree traversal algorithms."""

from collections import deque


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


def ordered_recursive(tree):
    """In-order depth-first-search, implemented as recursive generator."""
    def _traverser(node):
        if node.left is not None:
            yield from ordered_recursive(node.left)
        yield node.value
        if node.right is not None:
            yield from ordered_recursive(node.right)
    return _traverse_tree_or_node(_traverser, tree)


def _traverse_tree_or_node(traverser, node):
    """Applies the traverser to the tree's root, or the given starting node."""
    if hasattr(node, 'root'):
        node = node.root
    return traverser(node) if node is not None else []
