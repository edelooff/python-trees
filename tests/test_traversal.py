import pytest

from sherwood.traversal import breadth_first, depth_first_inorder, ordered_iterative
from sherwood.trees.avl import AVLTree


@pytest.fixture(params=[depth_first_inorder, ordered_iterative])
def in_order_traverser(request):
    """Returns an in-order traverser."""
    return request.param


@pytest.mark.parametrize(
    "traverser", [breadth_first, depth_first_inorder, ordered_iterative]
)
def test_empty_tree_traversal(traverser):
    assert list(traverser(AVLTree())) == []


@pytest.mark.parametrize(
    "tree, expected",
    [
        (AVLTree([4, 2, 6, 1, 3, 5, 7]), [1, 2, 3, 4, 5, 6, 7]),
        (AVLTree([4, 2, 6, 1, 5, 7]), [1, 2, 4, 5, 6, 7]),
        (AVLTree([4, 2, 6, 3, 5, 7]), [2, 3, 4, 5, 6, 7]),
        (AVLTree(range(30, 100)), list(range(30, 100))),
    ],
)
def test_ordered_traversal(in_order_traverser, tree, expected):
    assert list(in_order_traverser(tree)) == expected


@pytest.mark.parametrize(
    "tree, child, expected",
    [
        (AVLTree([4, 2, 6, 1, 3]), "left", [1, 2, 3]),
        (AVLTree([4, 2, 6, 5, 7]), "right", [5, 6, 7]),
        (AVLTree([4, 2, 6, 1]), "left", [1, 2]),
        (AVLTree([4, 2, 6, 5]), "right", [5, 6]),
    ],
)
def test_partial_ordered_traversal(in_order_traverser, tree, child, expected):
    subtree = getattr(tree.root, child)
    assert list(in_order_traverser(subtree)) == expected


@pytest.mark.parametrize(
    "rank_order", [[4, 2, 6, 1, 3, 5, 7], [4, 2, 6, 9], [4, 2, 6, 1]]
)
def test_rank_ordered_traversal(rank_order):
    tree = AVLTree(rank_order)
    assert list(breadth_first(tree)) == rank_order


@pytest.mark.parametrize(
    "tree, child, expected",
    [
        (AVLTree([4, 2, 6, 1, 3]), "left", [2, 1, 3]),
        (AVLTree([4, 2, 6, 5, 7]), "right", [6, 5, 7]),
        (AVLTree([4, 2, 6, 1]), "left", [2, 1]),
        (AVLTree([4, 2, 6, 5]), "right", [6, 5]),
    ],
)
def test_partial_rank_ordered_traversal(tree, child, expected):
    subtree = getattr(tree.root, child)
    assert list(breadth_first(subtree)) == expected
