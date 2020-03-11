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


@pytest.mark.parametrize(
    'insert, expected', [
        ((1, 2, 3), (2, 1, 3)),  # rotate left
        ((3, 2, 1), (2, 1, 3)),  # rotate right
        ((1, 3, 2), (2, 1, 3)),  # rotate right-left
        ((3, 1, 2), (2, 1, 3)),  # rotate left-right
    ]
)
def test_basic_rotations(Tree, insert, expected):
    """Tests basic tree rotations and resulting balance."""
    tree = Tree(insert)
    root, left, right = expected
    assert tree.root.value == root
    assert tree.root.left.value == left
    assert tree.root.right.value == right
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_double_rotation(Tree):
    tree = Tree(5, 4, 3, 2, 1)
    assert tree.root.value == 4
    assert tree.root.right.value == 5
    assert tree.root.left.value == 2
    assert tree.root.left.left.value == 1
    assert tree.root.left.right.value == 3
