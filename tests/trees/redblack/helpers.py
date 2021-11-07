from __future__ import annotations

from typing import Iterable, Union

from sherwood.trees.redblack import Color, RBNode, RedBlackTree, is_black


def assert_invariants(node):
    """Asserts the Red-Black tree invariants for the given node and all child nodes

    - Asserts that the node's color is either `Color.red` or `Color.black`;
    - Asserts children of a red colored node are both colored black;
    - Asserts that all paths from the node down to any of the leaves passes
      through an equal number of black-colored nodes;
    - Asserts that the left child (if any) is smaller, and the inverse for the right
    """
    if node is None:
        return

    assert node.color in Color
    if node.color is Color.red:
        assert is_black(node.left)
        assert is_black(node.right)

    # All paths have the same number of black-colored nodes in them (black-depth)
    paths = list(paths_to_leaf(node))
    assert len(set(map(black_depth, paths))) == 1

    # Base binary tree validation and recursive checks down
    if node.left is not None:
        assert node.left.value < node.value
        assert_invariants(node.left)
    if node.right is not None:
        assert node.value < node.right.value
        assert_invariants(node.right)


def black_depth(path):
    """Returns the count of black nodes in an iterable."""
    return sum(map(is_black, path))


def paths_to_leaf(node):
    def _dfs(node, stack):
        if node is None:
            yield stack
        else:
            yield from _dfs(node.left, stack + (node,))
            yield from _dfs(node.right, stack + (node,))

    yield from _dfs(node, ())


def pre_order(tree):
    """Returns a pre-order tree traversal as a list."""

    def _traversal(node):
        if node is not None:
            yield node.value
            yield from _traversal(node.left)
            yield from _traversal(node.right)

    return list(_traversal(tree.root))


def tree_from_values_and_colors(colored_nodes: Iterable[Union[int, Color]]):
    """Constructs a tree from rank-order values and node colors."""

    def node_generator(values_colors):
        stream = iter(values_colors)
        for value, color in zip(stream, stream):
            yield RBNode(value=value, color=color)

    def attach(root, new_node):
        if new_node.value < root.value:
            if root.left is not None:
                return attach(root.left, new_node)
            root.left = new_node
        else:
            if root.right is not None:
                return attach(root.right, new_node)
            root.right = new_node

    inodes = node_generator(colored_nodes)
    tree = RedBlackTree()
    tree.root = next(inodes)
    for node in inodes:
        attach(tree.root, node)
    assert_invariants(tree.root)
    return tree


def assert_tree_deletion(tree, target_value):
    """Deleting the given value from the tree and asserts correct operation:

    1) Invariants are maintained after the delete has been performed
    2) The deleted value is no longer in the tree
    3) The tree has shrunk by exactly 1 node
    """
    tree_length = len(pre_order(tree))
    tree.delete(target_value)
    assert_invariants(tree.root)
    assert target_value not in tree
    assert len(pre_order(tree)) == tree_length - 1
