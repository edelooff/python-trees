import pytest


@pytest.fixture
def tree():
    from avl import AVLTree
    return AVLTree()


def test_single_item_tree(tree):
    tree.insert(5)
    assert 5 in tree


def test_double_insert_exception(tree):
    tree.insert(5)
    with pytest.raises(ValueError):
        tree.insert(5)


def test_multi_item_insert(tree):
    numbers = 8, 6, 10, 7
    for num in numbers:
        tree.insert(num)
    for num in numbers:
        assert num in tree


def test_rotate_right(tree):
    tree.insert(3)
    tree.insert(2)
    tree.insert(1)
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3


def test_rotate_left(tree):
    tree.insert(1)
    tree.insert(2)
    tree.insert(3)
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3


def test_rotate_left_right(tree):
    tree.insert(3)
    tree.insert(1)
    tree.insert(2)
    # Double rotation completed with middle value at root
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_rotate_right_left(tree):
    tree.insert(1)
    tree.insert(3)
    tree.insert(2)
    # Double rotation completed with middle value at root
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_complex(tree):
    for num in (5, 4, 3, 2, 1):
        tree.insert(num)
    root = tree.root
    assert root.value == 4
    assert root.right.value == 5
    assert root.left.value == 2
    assert root.left.left.value == 1
    assert root.left.right.value == 3
