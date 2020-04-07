"""Basic tree traversal algorithms."""

from collections import deque


def ordered_iterative(tree):
    """In-order depth-first-search, implemented as iterative generator."""
    def _traverser(node):
        backtracking = False
        current = node
        parents = deque([None])
        while current is not None:
            if not backtracking and current.left is not None:
                parents.append(current)
                current = current.left
                continue
            yield current.value
            if current.right is not None:
                backtracking = False
                current = current.right
                continue
            backtracking = True
            current = parents.pop()
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
        return traverser(node.root)
    return traverser(node)
