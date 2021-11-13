from collections import deque
from dataclasses import dataclass
from typing import (
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from pydot import Dot, Edge
from pydot import Node as DotNode

from ..typing import Node
from .context import DrawContext

# Type aliases
DotValue = Union[float, int, str]
DotAttrDict = Dict[str, DotValue]
DotAttrs = Iterator[Tuple[str, DotValue]]
EdgeAttributeGenerator = Callable[[DrawContext, Node, Node], DotAttrs]
NodeAttributeGenerator = Callable[[DrawContext, Node], DotAttrs]
Renderer = Callable[[Node, Optional[Set[Node]], float], Dot]


@dataclass
class TreeRenderer:
    edge_attr_funcs: Sequence[EdgeAttributeGenerator] = ()
    node_attr_funcs: Sequence[NodeAttributeGenerator] = ()

    edge_defaults: ClassVar[DotAttrDict] = {
        "color": "#222222",
        "dir": "none",
        "penwidth": 2,
    }
    extra_edge_defaults: ClassVar[DotAttrDict] = {
        "dir": "forward",
        "arrowsize": 0.75,
        "style": "dashed",
    }
    graph_defaults: ClassVar[DotAttrDict] = {
        "bgcolor": "#ffffff00",
        "nodesep": 0.3,
        "ranksep": 0.2,
    }
    node_defaults: ClassVar[DotAttrDict] = {
        "color": "#222222",
        "fillcolor": "#667788",
        "fontcolor": "#ffffff",
        "fontname": "ubuntu mono bold",
        "fontsize": 16,
        "penwidth": 2,
        "shape": "circle",
        "style": "filled",
    }

    def __call__(
        self,
        root: Node,
        marked_nodes: Optional[Set[Node]] = None,
        marked_hue: float = 0,
        extra_edges: Optional[List[Tuple[Node, Node]]] = (),
    ) -> Dot:
        """Returns a Dot graph for the tree starting at the given node.

        An optional selection of marked nodes may be provided. The rendering
        of these marked nodes is controlled entirely by the node/edge_attr_funcs.
        """
        context = self.new_context(marked_nodes or set(), marked_hue)
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
        for source, target in extra_edges:
            self.draw_extra_edge(context, source, target)
        return context.graph

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

    def draw_extra_edge(self, context: DrawContext, source: Node, target: Node) -> None:
        """Draws additional edge between nodes in the context edge_color."""
        edge_attrs = dict(**self.extra_edge_defaults, color=context.edge_color)
        context.graph.add_edge(Edge(str(id(source)), str(id(target)), **edge_attrs))

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

    def new_context(self, marked_nodes: Set[Node], marked_hue: float) -> DrawContext:
        graph = Dot(**self.graph_defaults)
        graph.set_edge_defaults(**self.edge_defaults)
        graph.set_node_defaults(**self.node_defaults)
        return DrawContext(graph, marked_nodes, marked_hue)
