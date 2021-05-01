from __future__ import annotations

from collections import deque
from colorsys import hls_to_rgb
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Set, Union

from pydot import Dot, Edge, Node

from ..trees.base import Node as BinaryNode

GRAPH_STYLE = {
    "bgcolor": "#ffffff00",
    "nodesep": 0.3,
    "ranksep": 0.2,
}
NODE_STYLE = {
    "fillcolor": "lightyellow",
    "fontname": "ubuntu mono bold",
    "fontsize": 18,
    "penwidth": 2,
    "shape": "circle",
    "style": "filled",
}


# Type helpers
DotStyle = Dict[str, Union[int, str]]
NodeDividerDrawer = Callable[[BinaryNode], None]
NodeDrawer = Callable[[BinaryNode, Optional[BinaryNode]], None]
NodeHeight = Callable[[Optional[BinaryNode]], int]


class MarkedNodes:
    def __init__(self, nodes: Set[BinaryNode], hue: float = 0):
        self.nodes = nodes
        self.edge_color = self._create_color(hue, 0.2)
        self.fill_color = self._create_color(hue, 0.92)

    def __contains__(self, other: Any) -> bool:
        return other in self.nodes

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return other.nodes <= self.nodes
        elif isinstance(other, set):
            return other <= self.nodes
        return NotImplemented

    @staticmethod
    def _create_color(hue: float, lightness: float) -> str:
        rgb_color = (round(val * 255) for val in hls_to_rgb(hue, lightness, 1))
        return "#{:02x}{:02x}{:02x}".format(*rgb_color)


def cached_node_height(cache_size: int) -> NodeHeight:
    """Provides a node-height function to return the height of its subtree.

    The height is determined recursively by going down the entire subtree.
    This avoids suboptimal results in trees where balance factors have not
    been updated yet. A cache ensures that determining the height of all
    subtrees in the tree only takes time on the order of the node count.
    """

    @lru_cache(maxsize=cache_size)
    def height(node: Optional[BinaryNode]) -> int:
        if node is None:
            return -1
        return 1 + max(height(node.left), height(node.right))

    return height


def tree_graph(
    root: BinaryNode,
    *,
    marked_nodes: Optional[MarkedNodes] = None,
    draw_height_imbalance: bool = True,
) -> Dot:
    """Returns a Dot graph for the tree starting at the given node.

    An optional selection of marked nodes will be graphed in a different fill
    color, as defined by the MarkedNodes instance. The `draw_height_imbalance`
    parameter controls whether children that start a taller subtree should be
    drawn with an emphasized edge.
    """
    graph = Dot(**GRAPH_STYLE)
    graph.set_edge_defaults(color="navy", dir="none", penwidth=2)
    graph.set_node_defaults(**NODE_STYLE)
    if marked_nodes is None:
        marked_nodes = MarkedNodes(set())
    node_height = cached_node_height(1024)
    draw_divider = _divider_drawer(graph, node_height)
    draw_node = _node_drawer(
        graph,
        marked_nodes=marked_nodes,
        height=node_height if draw_height_imbalance else None,
    )
    draw_node(root, None)
    nodes = deque([root])
    while nodes:
        node = nodes.popleft()
        if node.left:
            draw_node(node.left, node)
            nodes.append(node.left)
        draw_divider(node)
        if node.right:
            draw_node(node.right, node)
            nodes.append(node.right)
    return graph


def _divider_drawer(graph: Dot, height: NodeHeight) -> NodeDividerDrawer:
    """Draws a vertical divider to distinguish left/right child nodes."""
    marker_style = {"label": "", "width": 0, "height": 0, "style": "invis"}

    def _divider(node: BinaryNode) -> None:
        target = str(id(node))
        for _ in range(height(node)):
            parent, target = target, f":{target}"
            graph.add_node(Node(target, **marker_style))
            graph.add_edge(Edge(parent, target, style="invis", weight=5))

    return _divider


def _node_drawer(
    graph: Dot, *, marked_nodes: MarkedNodes, height: Optional[NodeHeight] = None
) -> NodeDrawer:
    """Returns a node drawing function, for the given graph and marked nodes.

    The returned function will draw the actual Dot node, and when given
    a parent node, an edge from the parent down to the target node.

    Alternate colors for marked nodes are determined based on the fill or
    edge color specified by the `marked_nodes` object.
    """

    def _tallest_child(node: BinaryNode, parent: BinaryNode) -> bool:
        """Returns whether the node is the tallest child of its parent."""
        if height is None:
            return True
        elif node is parent.left:
            return height(node) > height(parent.right)
        else:
            return height(node) > height(parent.left)

    def _draw(node: BinaryNode, parent: Optional[BinaryNode]) -> None:
        node_options = {"label": str(node.value)}
        if node in marked_nodes:
            node_options["fillcolor"] = marked_nodes.fill_color
        graph.add_node(Node(str(id(node)), **node_options))
        if parent is not None:
            style: DotStyle = {"penwidth": 4 if _tallest_child(node, parent) else 2}
            if {node, parent} <= marked_nodes:
                style["color"] = marked_nodes.edge_color
            graph.add_edge(Edge(str(id(parent)), str(id(node)), **style))

    return _draw
