import pytest


@pytest.fixture
def Tree():
    from avl import AVLTree
    return AVLTree


@pytest.fixture
def tree(Tree):
    return Tree()


def test_tree_insert(tree):
    tree.insert(5)
    assert 5 in tree


def test_tree_bulk_insert(tree):
    tree.bulk_insert([1, 2])
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_list(Tree):
    tree = Tree([1, 2])
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_iter(Tree):
    tree = Tree(range(1, 3))
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_params(Tree):
    tree = Tree(1, 2)
    assert 1 in tree
    assert 2 in tree


def test_double_insert_exception(tree):
    tree.insert(5)
    with pytest.raises(ValueError):
        tree.insert(5)


def test_multi_item_insert(tree):
    numbers = 8, 6, 10, 7
    tree.bulk_insert(numbers)
    for num in numbers:
        assert num in tree


def test_rotate_right(tree):
    tree.bulk_insert([3, 2, 1])
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3


def test_rotate_left(tree):
    tree.bulk_insert([1, 2, 3])
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3


def test_rotate_left_right(tree):
    tree.bulk_insert([3, 1, 2])
    # Double rotation completed with middle value at root
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_rotate_right_left(tree):
    tree.bulk_insert([1, 3, 2])
    # Double rotation completed with middle value at root
    assert tree.root.value == 2
    assert tree.root.left.value == 1
    assert tree.root.right.value == 3
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_complex(tree):
    tree.bulk_insert([5, 4, 3, 2, 1])
    root = tree.root
    assert root.value == 4
    assert root.right.value == 5
    assert root.left.value == 2
    assert root.left.left.value == 1
    assert root.left.right.value == 3
