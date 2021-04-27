from __future__ import annotations

from collections import deque
from colorsys import hls_to_rgb
from dataclasses import dataclass
from functools import lru_cache
from multiprocessing import Pool
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
)

from pydot import Dot, Edge, Node

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


class BinaryNode:
    def __init__(self, value: Any):
        self.value = value
        self.left: Optional[BinaryNode] = None
        self.right: Optional[BinaryNode] = None


# Type helpers
NodeDividerDrawer = Callable[[BinaryNode], None]
NodeDrawer = Callable[[BinaryNode, Optional[BinaryNode]], None]
NodeHeight = Callable[[Optional[BinaryNode]], int]


@dataclass
class AnimationFrame:
    root: BinaryNode
    highlighted_nodes: Set[BinaryNode]
    highlight_hue: float = 0

    @classmethod
    def from_serialized(cls, frame: SerialFrame) -> AnimationFrame:
        ivalues = iter(frame.serialization)
        root = node = BinaryNode(next(ivalues))
        marked_nodes = {root} if 0 in frame.node_indices else set()
        stack = []
        for idx, (branch_id, value) in enumerate(zip(ivalues, ivalues), 1):
            if branch_id == 0:
                stack.append(node)
                node.left = node = BinaryNode(value)
            else:
                for _ in range(1, branch_id):
                    node = stack.pop()
                node.right = node = BinaryNode(value)
            if idx in frame.node_indices:
                marked_nodes.add(node)
        return cls(root, marked_nodes, frame.hue)

    def serialize(self) -> SerialFrame:
        serialization, node_indices = [], []
        cur_branch = 0
        for node_index, (node, new_branch) in enumerate(dfs_branch_encoded(self.root)):
            if node in self.marked_nodes:
                node_indices.append(node_index)
            change, cur_branch = 1 + cur_branch - new_branch, new_branch
            serialization.append(change)
            serialization.append(node.value)
        return SerialFrame(serialization[1:], node_indices, self.highlight_hue)

    @property
    def marked_nodes(self) -> MarkedNodes:
        return MarkedNodes(self.highlighted_nodes, hue=self.highlight_hue)

    def render(self, name: str) -> None:
        graph = tree_graph(self.root, marked_nodes=self.marked_nodes)
        graph.write_png(name)


class SerialFrame(NamedTuple):
    serialization: List[Union[Any, int]]
    node_indices: List[int]
    hue: float


def dfs_branch_encoded(
    node: Optional[BinaryNode], branch_id: int = 0
) -> Iterator[Tuple[BinaryNode, int]]:
    if node is not None:
        yield node, branch_id
        yield from dfs_branch_encoded(node.left, branch_id=branch_id + 1)
        yield from dfs_branch_encoded(node.right, branch_id=branch_id)


class EventAnimator:
    def __init__(self, base_name: str):
        self._frame_count = 0
        self.base_name = base_name
        self.workers = Pool()

    def graph_delete(self, topic: str, event: Any) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.9))

    def graph_insert(self, topic: str, event: Any) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.4))

    def graph_rebalanced(self, topic: str, event: Any) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.6))

    def graph_rotation(self, topic: str, event: Any) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.7))

    def _render(self, frame: AnimationFrame) -> None:
        self.workers.apply_async(self.draw_graph, (frame.serialize(), self.frame_name))

    @property
    def frame_name(self) -> str:
        self._frame_count += 1
        return f"{self.base_name}_{self._frame_count}.png"

    def finish(self) -> None:
        """Closes the worker pool for additional jobs and waits for them to finish."""
        self.workers.close()
        self.workers.join()

    @staticmethod
    def draw_graph(serialized_frame: SerialFrame, name: str) -> None:
        """Multiprocess worker function to do the actual work of image rendering."""
        frame = AnimationFrame.from_serialized(serialized_frame)
        frame.render(name)


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
            style = {"penwidth": 4 if _tallest_child(node, parent) else 2}
            if {node, parent} <= marked_nodes:
                style["color"] = marked_nodes.edge_color
            graph.add_edge(Edge(str(id(parent)), str(id(node)), **style))

    return _draw
