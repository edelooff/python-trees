from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterator, Optional, Sequence, Set, Tuple, Union

from pydot import Dot, Edge, Node as DotNode

from ..typing import Node
from .context import DrawContext

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

# Type aliases
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
