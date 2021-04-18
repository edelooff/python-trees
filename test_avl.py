import pytest


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


def pre_order(tree):
    """Returns a pre-order tree traversal as a list."""

    def _traversal(node):
        if node is not None:
            yield node.value
            yield from _traversal(node.left)
            yield from _traversal(node.right)

    return list(_traversal(tree.root))


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
    "insert, expected",
    [
        pytest.param([1, 2, 3], [2, 1, 3], id="left rotation"),
        pytest.param([3, 2, 1], [2, 1, 3], id="right rotation"),
        pytest.param([1, 3, 2], [2, 1, 3], id="right-left rotation"),
        pytest.param([3, 1, 2], [2, 1, 3], id="left-right rotation"),
    ],
)
def test_basic_rotations(Tree, insert, expected):
    """Tests basic tree rotations and resulting balance."""
    tree = Tree(insert)
    assert_avl_invariants(tree.root)
    assert pre_order(tree) == expected


def test_double_rotation(Tree):
    tree = Tree(5, 4, 3, 2, 1)
    assert_avl_invariants(tree.root)
    assert pre_order(tree) == [4, 2, 1, 3, 5]


def test_delete_nonexisting(tree):
    """Tests deletion of nonexisting key raises KeyError."""
    tree.insert(1)
    with pytest.raises(KeyError):
        tree.delete(2)


def test_delete_root(tree):
    """Tests deletion of singular root node."""
    tree.insert(1)
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
def test_delete_trivial(Tree, insert, delete, expected):
    """Tests deletion of root/leaf nodes requiring no rotation."""
    tree = Tree(insert)
    tree.delete(delete)
    assert delete not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


@pytest.mark.parametrize(
    "insert, deletes, expected",
    [
        ([2, 1, 3], [2], [1, 3]),  # Implementation-defined, prefer left node
        ([3, 2, 4, 1, 5], [2, 4], [3, 1, 5]),
        ([3, 2, 4, 1, 5], [3, 4], [2, 1, 5]),
        ([3, 1, 5, 2, 4], [1, 5], [3, 2, 4]),
        ([4, 2, 6, 1, 3, 5], [4, 1, 6], [3, 2, 5]),
    ],
)
def test_delete_attach_without_rotation(Tree, insert, deletes, expected):
    """Tests selective pruning of nodes and reattaching them to parents."""
    tree = Tree(insert)
    for key in deletes:
        tree.delete(key)
    assert key not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


def test_delete_reattach(Tree):
    """Removing the root from a 2-depth V should reattach nodes correctly."""
    tree = Tree(3, 2, 4, 1, 5)
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
def test_delete_single_rotation(Tree, insert, delete, expected):
    """Tests deletion resulting in a single rotation."""
    tree = Tree(insert)
    tree.delete(delete)
    assert delete not in tree
    assert pre_order(tree) == expected
    assert_avl_invariants(tree.root)


def test_delete_double_rotation(Tree):
    """Tests deletion resulting in a double rotation."""
    tree = Tree(16, 8, 24, 4, 12, 20, 28, 2, 6, 10, 32, 1, 3)
    tree.delete(20)
    assert 20 not in tree
    assert tree.root.value == 8
    assert tree.root.left.value == 4
    assert tree.root.right.value == 16
    assert_avl_invariants(tree.root)
