import pytest

from sherwood.trees.base import Branch
from sherwood.trees.redblack import Color, RBNode, invert_color, is_black, replace_child

BLACK, RED = Color.black, Color.red


@pytest.mark.parametrize("color, expected_inverse", [(BLACK, RED), (RED, BLACK)])
def test_color_inverse(color, expected_inverse):
    """Asserts Color.inverse method returns expected enum members."""
    assert color.inverse is expected_inverse


@pytest.mark.parametrize(
    "nodes, colors",
    [
        pytest.param([RBNode(1, color=RED)], [BLACK], id="single red"),
        pytest.param([RBNode(1, color=BLACK)], [RED], id="single black"),
        pytest.param(
            [RBNode(1, color=BLACK), RBNode(3, color=RED), RBNode(2, color=BLACK)],
            [RED, BLACK, RED],
            id="multiple nodes",
        ),
        pytest.param(
            [None, RBNode(1, color=RED), None, None, RBNode(2, color=BLACK)],
            [BLACK, RED],
            id="mixed nodes and Nones",
        ),
    ],
)
def test_invert_color(nodes, colors):
    """Asserts correct filtering and in-place swapping of `invert_color` function."""
    invert_color(*nodes)
    assert [node.color for node in nodes if node is not None] == colors


@pytest.mark.parametrize(
    "node, expected",
    [
        pytest.param(RBNode(value=1, color=BLACK), True),
        pytest.param(RBNode(value=1, color=RED), False),
        pytest.param(None, True),
    ],
)
def test_is_black(node, expected):
    """Asserts correct operation of `is_black` function."""
    assert is_black(node) is expected


@pytest.mark.parametrize("branch", Branch)
@pytest.mark.parametrize("replacement", [None, RBNode(2, color=RED)])
def test_replace_child(branch, replacement):
    """Asserts correct pruning or replacement in `replace_child` function."""
    parent = RBNode(4, color=BLACK)
    child = RBNode(3, color=RED)
    setattr(parent, branch.name, child)
    replace_child(child, parent, replacement)
    assert getattr(parent, branch.name) is replacement
