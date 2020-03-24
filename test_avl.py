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


def test_delete_nonexisting(tree):
    """Tests deletion of nonexisting key raises KeyError."""
    tree.insert(1)
    with pytest.raises(KeyError):
        tree.delete(2)


def test_delete_root(tree):
    """Tests deletion of singular root node."""
    tree.insert(1)
    tree.delete(1)
    assert tree.root is None


@pytest.mark.parametrize(
    'insert, delete, exp_root, exp_balance', [
        ((1, 2), 1, 2, 0),
        ((1, 2), 2, 1, 0),
        ((4, 3), 3, 4, 0),
        ((4, 3), 4, 3, 0),
        ((2, 1, 3), 1, 2, 1),
        ((2, 1, 3), 2, 1, 1),  # Implementation-defined, prefer left node
        ((2, 1, 3), 3, 2, -1),
    ]
)
def test_delete_simple(Tree, insert, delete, exp_root, exp_balance):
    """Tests deletion of root/leaf nodes requiring no rotation."""
    tree = Tree(insert)
    tree.delete(delete)
    assert tree.root.value == exp_root
    assert tree.root.balance == exp_balance


@pytest.mark.parametrize(
    'insert, deletes, expected', [
        ((3, 2, 4, 1, 5), (2, 4), (3, 1, 5)),
        ((3, 2, 4, 1, 5), (3, 4), (2, 1, 5)),
        ((3, 1, 5, 2, 4), (1, 5), (3, 2, 4)),
        ((4, 2, 6, 1, 3, 5), (4, 1, 6), (3, 2, 5)),
    ]
)
def test_delete_attach_without_rotation(Tree, insert, deletes, expected):
    """Tests selective pruning of nodes and reattaching them to parents."""
    tree = Tree(insert)
    for key in deletes:
        tree.delete(key)
    root, left, right = expected
    assert tree.root.value == root
    assert tree.root.left.value == left
    assert tree.root.right.value == right
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_delete_reattach(Tree):
    """Removing the root from a 2-depth V should reattach nodes correctly."""
    tree = Tree(3, 2, 4, 1, 5)
    tree.delete(3)
    assert tree.root.value == 2
    assert tree.root.right.value == 4
    assert tree.root.left.value == 1


def test_delete_reattach_right(Tree):
    """Removing the root from a 2-depth V should reattach nodes correctly."""
    tree = Tree(3, 2, 4, 5)
    tree.delete(3)
    assert tree.root.value == 4
    assert tree.root.right.value == 5
    assert tree.root.left.value == 2


@pytest.mark.parametrize(
    'insert, delete, expected', [
        ((4, 2, 6, 7), 2, (6, 4, 7)),  # rotate left
        ((4, 2, 6, 1), 6, (2, 1, 4)),  # rotate right
        ((4, 2, 6, 5), 2, (5, 4, 6)),  # rotate right-left
        ((4, 2, 6, 3), 6, (3, 2, 4)),  # rotate left-right
    ]
)
def test_delete_single_rotation(Tree, insert, delete, expected):
    """Tests deletion resulting in a single rotation."""
    tree = Tree(insert)
    tree.delete(delete)
    root, left, right = expected
    assert tree.root.value == root
    assert tree.root.left.value == left
    assert tree.root.right.value == right
    # Tree should be fully balanced
    assert tree.root.balance == 0
    assert tree.root.left.balance == 0
    assert tree.root.right.balance == 0


def test_delete_double_rotation(Tree):
    """Tests deletion resulting in a double rotation."""
    tree = Tree(16, 8, 24, 4, 12, 20, 28, 2, 6, 10, 32, 1, 3)
    tree.delete(20)
    assert tree.root.value == 8
    assert tree.root.left.value == 4
    assert tree.root.right.value == 16
    assert tree.root.balance == 0
    assert tree.root.left.balance == -1
    assert tree.root.right.balance == 0
