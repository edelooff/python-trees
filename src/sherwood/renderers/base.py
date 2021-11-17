from collections import deque
from dataclasses import dataclass
from typing import (
    Callable,
    ClassVar,
    Deque,
    Dict,
    Iterator,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from pydot import Dot, Edge
from pydot import Node as DotNode

from ..trees.base import Branch
from ..typing import Node
from .context import DrawContext

# Type aliases
DotValue = Union[float, int, str]
DotAttrDict = Dict[str, DotValue]
DotAttrs = Iterator[Tuple[str, DotValue]]
EdgeAttributeGenerator = Callable[[DrawContext, Node, Node], DotAttrs]
NodeAttributeGenerator = Callable[[DrawContext, Node], DotAttrs]
Renderer = Callable[[Node, Set[Node], float, Sequence[Tuple[Node, Node]]], Dot]


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
    hidden_node: ClassVar[DotAttrDict] = {
        "label": "",
        "width": 0,
        "height": 0,
        "style": "invis",
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
        marked_nodes: Set[Node],
        marked_hue: float = 0,
        extra_edges: Sequence[Tuple[Node, Node]] = (),
    ) -> Dot:
        """Returns a Dot graph for the tree starting at the given node.

        An optional selection of marked nodes may be provided. The rendering
        of these marked nodes is controlled entirely by the node/edge_attr_funcs.
        """
        context = self.new_context(marked_nodes or set(), marked_hue)
        self.draw_node(context, root, None)
        nodes: Deque[Optional[Node]] = deque([root])
        while nodes:
            if (node := nodes.popleft()) is not None:
                nodes.append(self.draw_child(context, node, Branch.left))
                self.draw_divider(context, node)
                nodes.append(self.draw_child(context, node, Branch.right))
        for source, target in extra_edges:
            self.draw_extra_edge(context, source, target)
        return context.graph

    def draw_child(
        self, context: DrawContext, node: Node, branch: Branch
    ) -> Optional[Node]:
        """Draws a node's child, based on the Branch direction.

        After adding the node, an edge is drawn from the parent down to the child.
        Additional graphviz attributes for the edge are derived from `edge_attrs`.
        If there is no child at the given branch direction, a hidden child is drawn.
        """
        if (child := getattr(node, branch.name)) is not None:
            self.draw_node(context, child, node)
            edge_attrs = dict(self.edge_attrs(context, child, node))
            context.graph.add_edge(Edge(str(id(node)), str(id(child)), **edge_attrs))
        elif getattr(node, branch.inverse.name):
            self.draw_missing_child(context, node)
        return child

    def draw_divider(self, context: DrawContext, node: Node) -> None:
        """Adds an invisible vertical divider to the graph in the DrawContext.

        This provides horizontal separation between left and right child nodes.
        This divider consists of a number of nodes equal to the 'height' of the
        given node and the nodes and edges to them are drawn invisibly.
        """
        target = str(id(node))
        for _ in range(context.height(node)):
            parent, target = target, f":{target}"
            context.graph.add_node(DotNode(target, **self.hidden_node))
            context.graph.add_edge(Edge(parent, target, style="invis", weight=5))

    def draw_extra_edge(self, context: DrawContext, source: Node, target: Node) -> None:
        """Draws additional edge between nodes in the context edge_color."""
        edge_attrs = dict(**self.extra_edge_defaults, color=context.edge_color)
        context.graph.add_edge(Edge(str(id(source)), str(id(target)), **edge_attrs))

    def draw_missing_child(self, context: DrawContext, parent: Node) -> None:
        """Adds an empty node and edge for nodes with a single child.

        This avoids quirky behavior from drawing additional edges in graphs
        where the extra edge would run past nodes with only a single child.
        """
        target = f":d{id(parent)}"
        context.graph.add_node(DotNode(target, **self.hidden_node))
        context.graph.add_edge(Edge(str(id(parent)), target, style="invis"))

    def draw_node(
        self, context: DrawContext, node: Node, parent: Optional[Node]
    ) -> None:
        """Draws the given node with attributes derived from `node_attrs`."""
        node_attrs = dict(self.node_attrs(context, node), label=str(node.value))
        context.graph.add_node(DotNode(str(id(node)), **node_attrs))

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
