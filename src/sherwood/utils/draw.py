from __future__ import annotations

from collections import deque
from colorsys import hls_to_rgb
from dataclasses import dataclass
from functools import cached_property, lru_cache
from typing import Any, Callable, Iterator, Optional, Sequence, Set, Tuple, Union

from pydot import Dot, Edge, Node as DotNode

from ..events.base import AnimationNode
from ..trees.base import Node
from ..trees.redblack import RBNode


GRAPH_STYLE = {
    "bgcolor": "#ffffff00",
    "nodesep": 0.3,
    "ranksep": 0.2,
}
NODE_STYLE = {
    "color": "#222222",
    "fillcolor": "#596e80",
    "fontcolor": "#ffffff",
    "fontname": "ubuntu mono bold",
    "fontsize": 16,
    "penwidth": 2,
    "shape": "circle",
    "style": "filled",
}


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

        The height is determined recursively by going down the entire subtree.
        This avoids suboptimal results in trees where balance factors have not
        been updated yet. A cache ensures that determining the height of all
        subtrees in the tree only takes time on the order of the node count.
        """

        @lru_cache(maxsize=1024)
        def height(node: Optional[Node]) -> int:
            if node is None:
                return -1
            return 1 + max(height(node.left), height(node.right))

        return height


# Type helpers
DotAttrs = Iterator[Tuple[str, Union[int, str]]]
EdgeAttributeGenerator = Callable[[DrawContext, Node, Node], DotAttrs]
NodeAttributeGenerator = Callable[[DrawContext, Node], DotAttrs]
Renderer = Callable[[Node, Optional[Set[Node]], float], Dot]


@dataclass
class TreeRenderer:
    edge_attr_funcs: Sequence[EdgeAttributeGenerator] = ()
    node_attr_funcs: Sequence[NodeAttributeGenerator] = ()

    def __call__(
        self,
        root: Node,
        marked_nodes: Optional[Set[Node]] = None,
        marked_hue: float = 0,
    ) -> Dot:
        """Returns a Dot graph for the tree starting at the given node.

        An optional selection of marked nodes may be provided. The rendering
        of these marked nodes is controlled entirely by the node/edge_attr_funcs.
        """
        graph = Dot(**GRAPH_STYLE)
        graph.set_edge_defaults(color="#222222", dir="none", penwidth=2)
        graph.set_node_defaults(**NODE_STYLE)
        if marked_nodes is None:
            marked_nodes = set()
        context = DrawContext(graph, marked_nodes, marked_hue)
        self.draw_node(context, root, None)
        nodes = deque([root])
        while nodes:
            node = nodes.popleft()
            if node.left:
                self.draw_node(context, node.left, node)
                nodes.append(node.left)
            self.draw_divider(context, node)
            if node.right:
                self.draw_node(context, node.right, node)
                nodes.append(node.right)
        return graph

    def draw_divider(self, context: DrawContext, node: Node) -> None:
        """Adds an invisible vertical divider to the graph in the DrawContext.

        This provides horizontal separation between left and right child nodes.
        This divider consists of a number of nodes equal to the 'height' of the
        given node and the nodes and edges to them are drawn invisibly.
        """
        marker_style = {"label": "", "width": 0, "height": 0, "style": "invis"}
        target = str(id(node))
        for _ in range(context.height(node)):
            parent, target = target, f":{target}"
            context.graph.add_node(DotNode(target, **marker_style))
            context.graph.add_edge(Edge(parent, target, style="invis", weight=5))

    def draw_node(
        self, context: DrawContext, node: Node, parent: Optional[Node]
    ) -> None:
        """Adds the given node to the graph in the DrawContext.

        When the parent argument is given and non-None, an edge is drawn from
        parent down to the given node. The node is labeled with the string
        representation of its value. Additional graphviz attributes for both
        the Node and Edge are derived from `node_attrs` and `edge_attrs` resp.
        """
        node_attrs = dict(self.node_attrs(context, node))
        node_attrs.setdefault("label", str(node.value))
        context.graph.add_node(DotNode(str(id(node)), **node_attrs))
        if parent is not None:
            edge_attrs = dict(self.edge_attrs(context, node, parent))
            context.graph.add_edge(Edge(str(id(parent)), str(id(node)), **edge_attrs))

    def edge_attrs(self, context: DrawContext, node: Node, parent: Node) -> DotAttrs:
        """Iterator of Dot attributes over all provided edge attribute functions."""
        for func in self.edge_attr_funcs:
            yield from func(context, node, parent)

    def node_attrs(self, context: DrawContext, node: Node) -> DotAttrs:
        """Iterator of Dot attributes over all provided node attribute functions."""
        for func in self.node_attr_funcs:
            yield from func(context, node)


def hls_to_html(hue: float, lightness: float, saturation: float) -> str:
    rgb_color = hls_to_rgb(hue, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(*(round(val * 255) for val in rgb_color))


def color_marked_node_edge(context: DrawContext, node: Node, parent: Node) -> DotAttrs:
    if {node, parent} <= context.marked_nodes:
        yield "color", context.edge_color


def imbalanced_edge_weight(context: DrawContext, node: Node, parent: Node) -> DotAttrs:
    """Increases the edge's pen width if the current node is the parent's tallest."""
    if node is parent.left and context.height(node) > context.height(parent.right):
        yield "penwidth", 3
    elif node is parent.right and context.height(node) > context.height(parent.left):
        yield "penwidth", 3


def outline_marked_node(context: DrawContext, node: Node) -> DotAttrs:
    if node in context.marked_nodes:
        yield "color", context.edge_color
        yield "peripheries", 2


def red_black_node_color(context: DrawContext, node: Node) -> DotAttrs:
    color: Any
    if isinstance(node, RBNode):
        color = node.color.name
    elif isinstance(node, AnimationNode):
        color = node.options.get("color")
    if color == "black":
        yield "fillcolor", "#555555"
    elif color == "red":
        yield "fillcolor", "#dd1133"


draw_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge],
    node_attr_funcs=[outline_marked_node],
)

draw_avl_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge, imbalanced_edge_weight],
    node_attr_funcs=[outline_marked_node],
)

draw_redblack_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge],
    node_attr_funcs=[outline_marked_node, red_black_node_color],
)
