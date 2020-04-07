import pytest

from avl import AVLTree


@pytest.fixture
def traverser():
    from traversal import ordered_recursive
    return ordered_recursive


@pytest.mark.parametrize('tree, expected', [
    (AVLTree(4, 2, 6, 1, 3, 5, 7), [1, 2, 3, 4, 5, 6, 7]),
    (AVLTree(4, 2, 6, 1, 5, 7), [1, 2, 4, 5, 6, 7]),
    (AVLTree(4, 2, 6, 3, 5, 7), [2, 3, 4, 5, 6, 7]),
    (AVLTree(range(30, 100)), list(range(30, 100))),
])
def test_ordered_traversal(traverser, tree, expected):
    assert list(traverser(tree)) == expected
