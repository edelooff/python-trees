"""Basic tree traversal algorithms."""


def ordered_iterative(tree):
    """In-order depth-first-search, implemented as iterative generator."""
    def _traverser(node):
        current = node
        explored_lefts = {None}
        parents = [None]
        while current is not None:
            if current.left not in explored_lefts:
                parents.append(current)
                current = current.left
                continue
            yield current.value
            explored_lefts.add(current)
            if current.right is not None:
                current = current.right
                continue
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
