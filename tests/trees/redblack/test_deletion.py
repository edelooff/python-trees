"""Tests for deletion from Red-Black trees and maintenance of invariants."""

from itertools import chain, repeat

import pytest

from sherwood.trees.redblack import Color, RedBlackTree

from .helpers import assert_tree_deletion, pre_order, tree_from_values_and_colors

B, R = Color.black, Color.red


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
    assert_tree_deletion(tree, delete)
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
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize(
    "nodes, delete",
    [
        pytest.param([4, B, 2, B, 6, B, 1, R], 2, id="tail @ left-left"),
        pytest.param([4, B, 2, B, 6, B, 3, R], 2, id="tail @ left-right"),
        pytest.param([4, B, 2, B, 6, B, 5, R], 2, id="tail @ right-left"),
        pytest.param([4, B, 2, B, 6, B, 7, R], 2, id="tail @ right-right"),
    ],
)
def test_delete_hoist_single_red(nodes, delete):
    tree = tree_from_values_and_colors(nodes)
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize(
    "nodes, delete",
    [
        pytest.param([4, B, 2, B, 6, R, 5, B, 7, B], 2, id="delete on left"),
        pytest.param([4, B, 2, R, 6, B, 1, B, 3, B], 6, id="delete on right"),
    ],
)
def test_delete_cousin_repainting(nodes, delete):
    tree = tree_from_values_and_colors(nodes)
    assert_tree_deletion(tree, delete)


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
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize("delete", range(1, 8))
def test_all_black_rebalancing(delete):
    values = [4, B, 2, B, 6, B, 1, B, 3, B, 5, B, 7, B]
    tree = tree_from_values_and_colors(values)
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize("delete", range(1, 16))
def test_all_black_rebalancing_recursive(delete):
    values = 8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15
    node_iter = chain.from_iterable(zip(values, repeat(Color.black)))
    tree = tree_from_values_and_colors(node_iter)
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize("delete", [6, 10])
def test_rebalance_subtree_under_root(delete):
    nodes = [8, R, 4, B, 12, B, 2, R, 6, B, 10, B, 14, R, 1, B, 3, B, 13, B, 15, B]
    tree = tree_from_values_and_colors(nodes)
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize("delete", [10, 12, 14])
@pytest.mark.parametrize(
    "tail",
    [
        pytest.param([2, R, 6, B, 10, B, 14, B, 1, B, 3, B], id="distant cousin"),
        pytest.param([2, B, 6, R, 10, B, 14, B, 5, B, 7, B], id="close cousin"),
    ],
)
def test_rebalance_left_cousin_subtree_under_root(delete, tail):
    nodes = [16, B, 8, R, 24, B, 4, B, 12, B, 20, B, 28, B]
    tree = tree_from_values_and_colors(nodes + tail)
    assert_tree_deletion(tree, delete)


@pytest.mark.parametrize("delete", [18, 20, 22])
@pytest.mark.parametrize(
    "tail",
    [
        pytest.param([18, B, 22, B, 26, B, 30, R, 29, B, 31, B], id="distant cousin"),
        pytest.param([18, B, 22, B, 26, R, 30, B, 25, B, 27, B], id="close cousin"),
    ],
)
def test_rebalance_right_cousin_subtree_under_root(delete, tail):
    nodes = [16, B, 8, B, 24, R, 4, B, 12, B, 20, B, 28, B]
    tree = tree_from_values_and_colors(nodes + tail)
    assert_tree_deletion(tree, delete)
