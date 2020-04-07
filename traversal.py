"""Basic tree traversal algorithms."""


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
