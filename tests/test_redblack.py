from __future__ import annotations

from itertools import cycle

import pytest

from sherwood.trees.redblack import Color, RedBlackTree


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
