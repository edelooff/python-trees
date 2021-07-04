from colorsys import hls_to_rgb
from dataclasses import dataclass
from functools import cached_property, lru_cache
from typing import Callable, Optional, Set

from pydot import Dot

from ..trees.base import Node


@dataclass
class DrawContext:
    graph: Dot
    marked_nodes: Set[Node]
    marked_hue: float

    @property
    def edge_color(self) -> str:
        return hls_to_html(self.marked_hue, 0.35, 0.75)

    @property
    def fill_color(self) -> str:
        return hls_to_html(self.marked_hue, 0.92, 0.75)

    @cached_property
    def height(self) -> Callable[[Optional[Node]], int]:
        """Provides a node-height function to return the height of its subtree.

        The height is determined by (recursively) going down left and right
        subtrees. This avoids incorrect results in AVL trees with unupdated
        balance factors, and works for trees without 'tallest child' metadata.

        A cache ensures that determining the height of any/all nodes in
        the trees takes no more than O(n) time across all lookups.
        """

        @lru_cache(maxsize=1024)
        def height(node: Optional[Node]) -> int:
            if node is None:
                return -1
            return 1 + max(height(node.left), height(node.right))

        return height


def hls_to_html(hue: float, lightness: float, saturation: float) -> str:
    rgb_color = hls_to_rgb(hue, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(*(round(val * 255) for val in rgb_color))
