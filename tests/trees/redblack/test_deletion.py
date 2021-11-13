"""Tests for deletion from Red-Black trees and maintenance of invariants."""

from itertools import chain, repeat

import pytest

from sherwood.trees.redblack import Color, RedBlackTree

from .helpers import assert_tree_deletion, tree_from_values_and_colors

B, R = Color.black, Color.red


def test_delete_nonexisting():
    """Tests deletion of nonexisting key raises KeyError."""
    tree = RedBlackTree()
    with pytest.raises(KeyError):
        tree.delete(2)


class TestTrivialDeletes:
    """Tests for trivial delete cases requiring no recoloring or rotations."""

    @pytest.mark.parametrize("color", Color)
    def test_delete_sole_root(self, color):
        """Tests deletion of singular root node."""
        tree = tree_from_values_and_colors([1, color])
        assert_tree_deletion(tree, 1)
        assert tree.root is None

    @pytest.mark.parametrize(
        "nodes, delete",
        [
            pytest.param([4, B, 6, R], 6, id="leaf of right-leaning line"),
            pytest.param([4, B, 2, R], 2, id="leaf of left-leaning line"),
            pytest.param([4, B, 2, R, 6, R], 2, id="left leaf of V-tree"),
            pytest.param([4, B, 2, R, 6, R], 6, id="right leaf of V-tree"),
        ],
    )
    def test_delete_dangling_red(self, nodes, delete):
        """Tests trivial removal of red dangling child."""
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "nodes, delete",
        [
            pytest.param([4, B, 2, R], 4, id="root with left child"),
            pytest.param([4, B, 6, R], 4, id="root with right child"),
            pytest.param([4, B, 2, R, 6, R], 4, id="root with two children"),
        ],
    )
    def test_delete_root_with_dangling_red(self, nodes, delete):
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "nodes",
        [
            pytest.param([4, B, 2, B, 6, B, 1, R, 7, R], id="branches spreading out"),
            pytest.param([4, B, 2, B, 6, B, 3, R, 5, R], id="branches bending in"),
        ],
    )
    @pytest.mark.parametrize("delete", [4, 2, 6])
    def test_non_leaf_swapped_for_red_leaf(self, nodes, delete):
        """Deleting a non-leaf initiates a swap with a trivially removed leaf."""
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)


class TestRecoloringDeletes:
    """Tests deletes requiring node recoloring but no tree rotations."""

    @pytest.mark.parametrize("delete", [4, 2, 6])
    def test_all_black_tree_recoloring(self, delete):
        nodes = [4, B, 2, B, 6, B]
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize("delete", range(1, 8))
    def test_all_black_tree_double_recoloring(self, delete):
        nodes = [4, B, 2, B, 6, B, 1, B, 3, B, 5, B, 7, B]
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize("delete", range(1, 16))
    def test_all_black_tree_triple_recoloring(self, delete):
        values = 8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15
        nodes = chain.from_iterable(zip(values, repeat(Color.black)))
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "nodes, delete",
        [
            pytest.param([4, R, 2, B, 6, B], 2, id="repaint root"),
            pytest.param([4, B, 2, B, 6, R, 5, B, 7, B], 5, id="repaint non-root"),
            pytest.param([4, B, 2, B, 6, R, 5, B, 7, B], 7, id="repaint non-root"),
        ],
    )
    def test_repaint_black_parent(self, nodes, delete):
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)


class TestRebalancingDeletes:
    """Tests deletes that include tree recoloring and rotations."""

    @pytest.mark.parametrize(
        "nodes, delete",
        [
            pytest.param([4, B, 2, B, 6, R, 5, B, 7, B], 2, id="root.left"),
            pytest.param([4, B, 2, R, 6, B, 1, B, 3, B], 6, id="root.right"),
            pytest.param(
                [8, R, 4, B, 12, B, 2, B, 6, R, 10, B, 14, B, 5, B, 7, B],
                2,
                id="child.left",
            ),
            pytest.param(
                [8, R, 4, B, 12, B, 2, R, 6, B, 10, B, 14, B, 1, B, 3, B],
                6,
                id="child.right",
            ),
        ],
    )
    def test_black_cousins_single_rotation(self, nodes, delete):
        """Both cousins of deleted node are black, only a single rotation required."""
        tree = tree_from_values_and_colors(nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "base_nodes",
        [
            pytest.param([4, R, 2, B, 6, B], id="anchor at root"),
            pytest.param([8, R, 4, B, 10, B, 2, B, 6, B, 9, B, 11, B], id="at child"),
        ],
    )
    @pytest.mark.parametrize(
        "tail_nodes, delete",
        [
            pytest.param([7, R], 2, id="left: distant cousin"),
            pytest.param([1, R], 6, id="right: distant cousin"),
            pytest.param([5, R], 2, id="left: close cousin"),
            pytest.param([3, R], 6, id="right: close cousin"),
            pytest.param([5, R, 7, R], 2, id="left: both cousins"),
            pytest.param([1, R, 3, R], 6, id="right: both cousins"),
        ],
    )
    def test_red_cousin_rotations(self, base_nodes, tail_nodes, delete):
        """Asserts rotations are performed and anchored correctly."""
        tree = tree_from_values_and_colors(base_nodes + tail_nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "tail_nodes, delete",
        [
            pytest.param([2, B, 6, B, 10, B, 14, R, 13, B, 15, B], 4, id="left dist."),
            pytest.param([2, B, 6, B, 10, R, 14, B, 9, B, 11, B], 4, id="left close"),
            pytest.param([2, R, 6, B, 10, B, 14, B, 1, B, 3, B], 10, id="right dist."),
            pytest.param([2, B, 6, R, 10, B, 14, B, 5, B, 7, B], 10, id="right close"),
        ],
    )
    def test_red_cousin_rotations_with_child_trees(self, tail_nodes, delete):
        """Asserts the red cousins keeps their child trees in appropriate positions."""
        tree = tree_from_values_and_colors([8, R, 4, B, 12, B] + tail_nodes)
        assert_tree_deletion(tree, delete)

    @pytest.mark.parametrize(
        "tail_nodes",
        [
            pytest.param([], id="base (single rotation)"),
            pytest.param([5, R, 7, R], id="close cousin rotation"),
            pytest.param([1, R, 3, R], id="distanc cousin rotation"),
        ],
    )
    def test_red_sibling_double_rotation(self, tail_nodes):
        base = [8, B, 4, R, 12, B, 2, B, 6, B]
        tree = tree_from_values_and_colors(base + tail_nodes)
        assert_tree_deletion(tree, 12)
