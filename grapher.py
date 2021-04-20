from __future__ import annotations

from collections import deque
from colorsys import hls_to_rgb
from functools import lru_cache
from multiprocessing import Pool
from typing import Callable

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


class EventAnimator:
    def __init__(self, base_name: str):
        self._frame_count = 0
        self.base_name = base_name
        self.workers = Pool()

    def graph_delete(self, topic, message) -> None:
        self._render(message["tree"], MarkedNodes({message["node"]}, hue=0.9))

    def graph_insert(self, topic, message) -> None:
        self._render(message["tree"], MarkedNodes({message["node"]}, hue=0.4))

    def graph_rebalanced(self, topic, message) -> None:
        root = message["root"]
        marks = MarkedNodes({root, root.left, root.right}, hue=0.6)
        self._render(message["tree"], marks)

    def graph_rotation(self, topic, message) -> None:
        self._render(message["tree"], MarkedNodes(message["nodes"], hue=0.7))

    def _render(self, root, marked_nodes: MarkedNodes) -> None:
        self.workers.apply_async(self.draw_graph, (root, marked_nodes, self.frame_name))

    @property
    def frame_name(self):
        self._frame_count += 1
        return f"{self.base_name}_{self._frame_count}.png"

    def finish(self):
        """Closes the worker pool for additional jobs and waits for them to finish."""
        self.workers.close()
        self.workers.join()

    @staticmethod
    def draw_graph(tree, marked_nodes, name):
        """Multiprocess worker function to do the actual work of image rendering."""
        graph = tree_graph(tree, marked_nodes=marked_nodes)
        graph.write_png(name)


class MarkedNodes:
    def __init__(self, nodes, hue: float = 0):
        self.nodes = nodes
        self.edge_color = self._create_color(hue, 0.2)
        self.fill_color = self._create_color(hue, 0.92)

    def __contains__(self, other) -> bool:
        return other in self.nodes

    def __ge__(self, other) -> bool:
        if isinstance(other, type(self)):
            return other.nodes <= self.nodes
        elif isinstance(other, set):
            return other <= self.nodes
        return NotImplemented

    @staticmethod
    def _create_color(hue, lightness) -> str:
        rgb_color = (round(val * 255) for val in hls_to_rgb(hue, lightness, 1))
        return "#{:02x}{:02x}{:02x}".format(*rgb_color)


def cached_node_height(cache_size: int) -> Callable:
    """Provides a node-height function to return the height of its subtree.

    The height is determined recursively by going down the entire subtree.
    This avoids suboptimal results in trees where balance factors have not
    been updated yet. A cache ensures that determining the height of all
    subtrees in the tree only takes time on the order of the node count.
    """

    @lru_cache(maxsize=cache_size)
    def height(node) -> int:
        if node is None:
            return -1
        return 1 + max(height(node.left), height(node.right))

    return height


def tree_graph(root, *, marked_nodes=None, draw_height_imbalance=True) -> Dot:
    """Returns a Dot graph for the tree starting at the given node.

    An optional selection of marked nodes will be graphed in a different fill
    color, as defined by the MarkedNodes instance. The `draw_height_imbalance`
    parameter controls whether children that start a taller subtree should be
    drawn with an emphasized edge.
    """
    graph = Dot(**GRAPH_STYLE)
    graph.set_edge_defaults(color="navy", dir="none", penwidth=2)
    graph.set_node_defaults(**NODE_STYLE)
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


def _divider_drawer(graph: Dot, height: Callable) -> Callable:
    """Draws a vertical divider to distinguish left/right child nodes."""
    marker_style = {"label": "", "width": 0, "height": 0, "style": "invis"}

    def _divider(node) -> None:
        target = str(id(node))
        for _ in range(height(node)):
            parent, target = target, f":{target}"
            graph.add_node(Node(target, **marker_style))
            graph.add_edge(Edge(parent, target, style="invis", weight=5))

    return _divider


def _node_drawer(graph: Dot, *, marked_nodes=None, height=None) -> Callable:
    """Returns a node drawing function, for the given graph and marked nodes.

    The returned function will draw the actual Dot node, and when given
    a parent node, an edge from the parent down to the target node.

    Alternate colors for marked nodes are determined based on the fill or
    edge color specified by the `marked_nodes` object.
    """

    def _tallest_child(node, parent) -> bool:
        """Returns whether the node is the tallest child of its parent."""
        if height is None:
            return True
        elif node is parent.left:
            return height(node) > height(parent.right)
        else:
            return height(node) > height(parent.left)

    def _draw(node, parent) -> None:
        node_options = {"label": str(node.value)}
        if marked_nodes is not None and node in marked_nodes:
            node_options["fillcolor"] = marked_nodes.fill_color
        graph.add_node(Node(str(id(node)), **node_options))
        if parent is not None:
            style = {"penwidth": 4 if _tallest_child(node, parent) else 2}
            if marked_nodes is not None and {node, parent} <= marked_nodes:
                style["color"] = marked_nodes.edge_color
            graph.add_edge(Edge(str(id(parent)), str(id(node)), **style))

    return _draw
