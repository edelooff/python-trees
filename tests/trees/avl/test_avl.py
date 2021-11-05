import pytest

from sherwood.trees.avl import AVLTree


def tree_height(node):
    if node is None:
        return 0
    return 1 + max(tree_height(node.left), tree_height(node.right))


def assert_avl_invariants(node):
    """Asserts the AVL tree invariants for the given node and all child nodes

    - Asserts that the node's balance is between -1 and +1
    - Asserts that the balance is equal to the attached subtree height difference
    - Asserts that the left child is smaller, right child is larger
    """
    assert node.balance in {-1, 0, 1}
    assert node.balance == tree_height(node.right) - tree_height(node.left)
    if node.left is not None:
        assert node.left.value < node.value
        assert_avl_invariants(node.left)
    if node.right is not None:
        assert node.value < node.right.value
        assert_avl_invariants(node.right)


def in_order(tree):
    """Returns an in-order tree traversal as a list."""

    def _traversal(node):
        if node is not None:
            yield from _traversal(node.left)
            yield node.value
            yield from _traversal(node.right)

    return list(_traversal(tree.root))


def pre_order(tree):
    """Returns a pre-order tree traversal as a list."""

    def _traversal(node):
        if node is not None:
            yield node.value
            yield from _traversal(node.left)
            yield from _traversal(node.right)

    return list(_traversal(tree.root))


def test_tree_insert():
    tree = AVLTree()
    tree.insert(5)
    assert 5 in tree


def test_instantiate_from_list():
    tree = AVLTree([1, 2])
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_iter():
    tree = AVLTree(range(1, 3))
    assert 1 in tree
    assert 2 in tree


def test_instantiate_from_string():
    tree = AVLTree("abc")
    assert "a" in tree
    assert "b" in tree
    assert "c" in tree


def test_double_insert_exception():
    tree = AVLTree([5])
    with pytest.raises(ValueError):
        tree.insert(5)


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
    """Tests basic tree rotations and resulting balance."""
    tree = AVLTree(insert)
    assert_avl_invariants(tree.root)
    assert pre_order(tree) == expected


def test_double_rotation():
    tree = AVLTree([5, 4, 3, 2, 1])
    assert_avl_invariants(tree.root)
    assert pre_order(tree) == [4, 2, 1, 3, 5]


def test_delete_nonexisting():
    """Tests deletion of nonexisting key raises KeyError."""
    tree = AVLTree()
    with pytest.raises(KeyError):
        tree.delete(2)


def test_delete_root():
    """Tests deletion of singular root node."""
    tree = AVLTree([1])
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
    tree = AVLTree(insert)
    tree.delete(delete)
    assert delete not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


@pytest.mark.parametrize(
    "insert, deletes, expected",
    [
        pytest.param([4, 2, 6, 1, 7], [2, 6], [4, 1, 7], id="remove middle from lines"),
        pytest.param([4, 2, 6, 3, 5], [2, 6], [4, 3, 5], id="remove middle from bends"),
        pytest.param([4, 2, 6, 1, 7], [4, 6], [2, 1, 7], id="remove root and left"),
        pytest.param([4, 2, 6, 1, 7], [4, 2], [6, 1, 7], id="remove root and right"),
        pytest.param([4, 2, 6, 1, 3, 5], [4, 2, 6], [3, 1, 5], id="hoist left (b)"),
        pytest.param([4, 2, 6, 1, 5, 7], [4, 2, 6], [5, 1, 7], id="hoist right (b)"),
    ],
)
def test_delete_attach_without_rotation(insert, deletes, expected):
    """Tests selective pruning of nodes and reattaching them to parents."""
    tree = AVLTree(insert)
    for key in deletes:
        tree.delete(key)
    assert key not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


def test_delete_reattach():
    """Removing the root from a 2-depth V should reattach nodes correctly."""
    tree = AVLTree([3, 2, 4, 1, 5])
    tree.delete(3)
    assert 3 not in tree
    assert pre_order(tree) == [2, 1, 4, 5]
    assert_avl_invariants(tree.root)


@pytest.mark.parametrize(
    "insert, delete, expected",
    [
        pytest.param([4, 2, 6, 7], 2, [6, 4, 7], id="left rotation"),
        pytest.param([4, 2, 6, 5, 7], 2, [6, 4, 5, 7], id="left (balanced) rotation"),
        pytest.param([4, 2, 6, 1], 6, [2, 1, 4], id="right rotation"),
        pytest.param([4, 2, 6, 1, 3], 6, [2, 1, 4, 3], id="right (balanced) rotation"),
        pytest.param([4, 2, 6, 5], 2, [5, 4, 6], id="right-left rotation"),
        pytest.param([4, 2, 6, 3], 6, [3, 2, 4], id="left-right rotation"),
    ],
)
def test_delete_single_rotation(insert, delete, expected):
    """Tests deletion resulting in a single rotation."""
    tree = AVLTree(insert)
    tree.delete(delete)
    assert delete not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


def test_delete_double_rotation():
    """Tests deletion resulting in a double rotation."""
    tree = AVLTree([16, 8, 24, 4, 12, 20, 28, 2, 6, 10, 32, 1, 3])
    tree.delete(20)
    assert 20 not in tree
    assert tree.root.value == 8
    assert tree.root.left.value == 4
    assert tree.root.right.value == 16
    assert_avl_invariants(tree.root)


@pytest.mark.parametrize(
    "insert, delete",
    [
        pytest.param([8, 4, 12, 2, 6, 14, 1], 6, id="right rot: left-heavy tail"),
        pytest.param([8, 4, 12, 2, 6, 14, 3], 6, id="right rot: right-heavy tail"),
        pytest.param([8, 4, 12, 2, 6, 14, 1, 3], 6, id="right rot: balanced tail"),
        pytest.param([8, 4, 12, 2, 10, 14, 13], 10, id="left rot: left-heavy tail"),
        pytest.param([8, 4, 12, 2, 10, 14, 15], 10, id="left rot: right-heavy tail"),
        pytest.param([8, 4, 12, 2, 10, 14, 13, 15], 10, id="left rot: balanced tail"),
        pytest.param([6, 4, 8, 2, 7, 10, 9, 11], 7, id="propagate balance left child"),
        pytest.param([6, 4, 8, 2, 5, 7, 1, 3], 6, id="propagate balance right child"),
    ],
)
def test_delete_rotation_under_root(insert, delete):
    tree = AVLTree(insert)
    tree.delete(delete)
    assert delete not in tree
    expected = sorted(insert)
    expected.remove(delete)
    assert in_order(tree) == expected
    assert_avl_invariants(tree.root)


@pytest.mark.parametrize(
    "insert, delete",
    [
        pytest.param([8, 4, 12, 2, 6, 14, 5], 14, id="left-right: left-heavy"),
        pytest.param([8, 4, 12, 2, 6, 14, 7], 14, id="left-right: right-heavy"),
        pytest.param([8, 4, 12, 2, 6, 14, 5, 7], 14, id="left-right: balanced"),
        pytest.param([8, 4, 12, 2, 10, 14, 9], 2, id="right-left: left-heavy"),
        pytest.param([8, 4, 12, 2, 10, 14, 11], 2, id="right-left: right-heavy"),
        pytest.param([8, 4, 12, 2, 10, 14, 9, 11], 2, id="right-left: balanced"),
    ],
)
def test_two_way_rotations_with_subtree_at_pivot(insert, delete):
    """Deletion causes a LR or RL rotation and the new subtree root has children."""
    tree = AVLTree(insert)
    tree.delete(delete)
    assert delete not in tree
    expected = sorted(insert)
    expected.remove(delete)
    assert in_order(tree) == expected
    assert_avl_invariants(tree.root)
