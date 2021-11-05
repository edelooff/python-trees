import pytest

from sherwood.trees.redblack import Color, RBNode, is_black

BLACK, RED = Color.black, Color.red


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
