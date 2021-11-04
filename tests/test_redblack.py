from __future__ import annotations

from itertools import chain, cycle, repeat
from typing import Iterable, Union

import pytest

from sherwood.trees.redblack import Color, RBNode, RedBlackTree

B, R = Color.black, Color.red


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
        assert node_is_black(node.left)
        assert node_is_black(node.right)

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
    return sum(1 for node in path if node.color is Color.black)
    return sum(map(node_is_black, path))


def node_is_black(node):
    """Returns whether a node is black, with NIL nodes (None) considered black."""
    return node is None or node.color is Color.black


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


def test_tree_insert():
    tree = RedBlackTree()
    tree.insert(5)
    assert 5 in tree


def test_instantiate_from_list():
    tree = RedBlackTree([1, 2])
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_iter():
    tree = RedBlackTree(range(1, 3))
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_string():
    tree = RedBlackTree("abc")
    assert "a" in tree
    assert "b" in tree
    assert "c" in tree


def test_double_insert_exception():
    tree = RedBlackTree([5])
    with pytest.raises(ValueError):
        tree.insert(5)


@pytest.mark.parametrize(
    "insert, expected_root_color, expected_pre_order",
    [
        pytest.param([4, 2], Color.black, [4, 2], id="left heavy"),
        pytest.param([4, 6], Color.black, [4, 6], id="right heavy"),
        pytest.param([4, 2, 6, 1], Color.red, [4, 2, 1, 6], id="row color swap"),
        pytest.param([4, 2, 6, 3], Color.red, [4, 2, 3, 6], id="row color swap"),
        pytest.param([4, 2, 6, 5], Color.red, [4, 2, 6, 5], id="row color swap"),
        pytest.param([4, 2, 6, 7], Color.red, [4, 2, 6, 7], id="row color swap"),
    ],
)
def test_rotationless_recoloring(insert, expected_root_color, expected_pre_order):
    """Tests recoloring of tree nodes without requiring rotations."""
    tree = RedBlackTree(insert)
    assert_invariants(tree.root)
    assert tree.root.color is expected_root_color
    assert pre_order(tree) == expected_pre_order


@pytest.mark.parametrize(
    "insert, expected",
    [
        pytest.param([1, 2, 3], [2, 1, 3], id="left rotation"),
        pytest.param([3, 2, 1], [2, 1, 3], id="right rotation"),
        pytest.param([1, 3, 2], [2, 1, 3], id="right-left rotation"),
        pytest.param([3, 1, 2], [2, 1, 3], id="left-right rotation"),
    ],
)
def test_basic_rotations(insert, expected):
    """Tests basic tree rotations."""
    tree = RedBlackTree(insert)
    assert_invariants(tree.root)
    assert pre_order(tree) == expected


@pytest.mark.parametrize(
    "initial, root_color, additional, new_root_color",
    [
        pytest.param([5, 6, 3, 4, 2], Color.red, 1, Color.black, id="left side"),
        pytest.param([2, 1, 4, 3, 5], Color.red, 6, Color.black, id="right side"),
    ],
)
def test_double_recolor(initial, root_color, additional, new_root_color):
    tree = RedBlackTree(initial)
    assert tree.root.color is root_color
    tree.insert(additional)
    assert tree.root.color is new_root_color


def test_triple_recolor():
    """Recoloring continues towards the root or until rotations are required."""

    def left_edge(node):
        yield node.value, node.color
        if node.left is not None:
            yield from left_edge(node.left)

    tree = RedBlackTree([13, 16, 8, 17, 15, 11, 5, 14, 12, 10, 6, 3, 9, 4, 2])
    red_root_values = zip([13, 8, 5, 3, 2], cycle([Color.red, Color.black]))
    assert list(left_edge(tree.root)) == list(red_root_values)
    tree.insert(1)
    black_root_values = zip([13, 8, 5, 3, 2, 1], cycle([Color.black, Color.red]))
    assert list(left_edge(tree.root)) == list(black_root_values)


def test_example():
    tree = RedBlackTree()
    for value in [43, 81, 95, 16, 28, 23, 63, 57]:
        tree.insert(value)
        assert_invariants(tree.root)


def test_delete_nonexisting():
    """Tests deletion of nonexisting key raises KeyError."""
    tree = RedBlackTree()
    with pytest.raises(KeyError):
        tree.delete(2)


def test_delete_root():
    """Tests deletion of singular root node."""
    tree = RedBlackTree([1])
    tree.delete(1)
    assert 1 not in tree
    assert tree.root is None


@pytest.mark.parametrize(
    "insert, delete, expected",
    [
        pytest.param([4, 6], 4, [6], id="root of right-leaning line"),
        pytest.param([4, 6], 6, [4], id="leaf of right-leaning line"),
        pytest.param([4, 2], 4, [2], id="root of left-leaning line"),
        pytest.param([4, 2], 2, [4], id="leaf of left-leaning line"),
        pytest.param([4, 2, 6], 2, [4, 6], id="left leaf of V-tree"),
        pytest.param([4, 2, 6], 6, [4, 2], id="right leaf of V-tree"),
    ],
)
def test_delete_trivial(insert, delete, expected):
    """Tests deletion of root/leaf nodes requiring no rotation."""
    tree = RedBlackTree(insert)
    tree.delete(delete)
    assert_invariants(tree.root)
    assert pre_order(tree) == expected


@pytest.mark.parametrize(
    "nodes, delete",
    [
        pytest.param([2, B, 1, B, 3, B], 1, id="delete left"),
        pytest.param([2, B, 1, B, 3, B], 3, id="delete right"),
    ],
)
def test_delete_recoloring(nodes, delete):
    tree = tree_from_values_and_colors(nodes)
    tree_length = len(pre_order(tree))
    tree.delete(delete)
    assert_invariants(tree.root)
    assert delete not in tree
    assert len(pre_order(tree)) == tree_length - 1


@pytest.mark.parametrize(
    "nodes, delete",
    [
        pytest.param([4, B, 2, B, 6, R, 5, B, 7, B], 2, id="delete on left"),
        pytest.param([4, B, 2, R, 6, B, 1, B, 3, B], 6, id="delete on right"),
    ],
)
def test_delete_cousin_repainting(nodes, delete):
    tree = tree_from_values_and_colors(nodes)
    tree_length = len(pre_order(tree))
    tree.delete(delete)
    assert_invariants(tree.root)
    assert delete not in tree
    assert len(pre_order(tree)) == tree_length - 1


@pytest.mark.parametrize("delete", [11, 12, 13])
@pytest.mark.parametrize(
    "nodes",
    [
        pytest.param(
            [8, R, 4, B, 12, B, 2, R, 6, B, 11, B, 13, B, 1, B, 3, B],
            id="left-left-leavy",
        ),
        pytest.param(
            [8, R, 4, B, 12, B, 2, B, 6, R, 11, B, 13, B, 5, B, 7, B],
            id="left-right-leavy",
        ),
        pytest.param(
            [16, R, 12, B, 20, B, 11, B, 13, B, 18, B, 22, R, 21, B, 23, B],
            id="right-right-heavy",
        ),
        pytest.param(
            [16, R, 12, B, 20, B, 11, B, 13, B, 18, R, 22, B, 17, B, 19, B],
            id="right-left-heavy",
        ),
    ],
)
def test_delete_case_cousin_rebalancing(nodes, delete):
    """Restores black-depth of tree by rotating at cousins of deleted node."""
    tree = tree_from_values_and_colors(nodes)
    tree_length = len(pre_order(tree))

    tree.delete(delete)
    assert_invariants(tree.root)
    assert delete not in tree
    assert len(pre_order(tree)) == tree_length - 1


@pytest.mark.parametrize("delete", range(1, 8))
def test_all_black_rebalancing(delete):
    values = [4, B, 2, B, 6, B, 1, B, 3, B, 5, B, 7, B]
    tree = tree_from_values_and_colors(values)
    tree_length = len(pre_order(tree))

    tree.delete(delete)
    assert_invariants(tree.root)
    assert delete not in tree
    assert len(pre_order(tree)) == tree_length - 1


@pytest.mark.parametrize("delete", range(1, 16))
def test_all_black_rebalancing_recursive(delete):
    values = 8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15
    node_iter = chain.from_iterable(zip(values, repeat(Color.black)))
    tree = tree_from_values_and_colors(node_iter)
    tree_length = len(pre_order(tree))

    tree.delete(delete)
    assert_invariants(tree.root)
    assert delete not in tree
    assert len(pre_order(tree)) == tree_length - 1
