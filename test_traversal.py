import pytest

from avl import AVLTree
from traversal import (
    ordered_iterative,
    ordered_recursive)


@pytest.fixture(params=[ordered_iterative, ordered_recursive])
def in_order_traverser(request):
    """Returns an in-order traverser."""
    return request.param


def test_empty_tree_traversal(in_order_traverser):
    assert list(in_order_traverser(AVLTree())) == []


@pytest.mark.parametrize('tree, expected', [
    (AVLTree(4, 2, 6, 1, 3, 5, 7), [1, 2, 3, 4, 5, 6, 7]),
    (AVLTree(4, 2, 6, 1, 5, 7), [1, 2, 4, 5, 6, 7]),
    (AVLTree(4, 2, 6, 3, 5, 7), [2, 3, 4, 5, 6, 7]),
    (AVLTree(range(30, 100)), list(range(30, 100))),
])
def test_ordered_traversal(in_order_traverser, tree, expected):
    assert list(in_order_traverser(tree)) == expected
