from collections import deque
from colorsys import hls_to_rgb
from functools import lru_cache

from pydot import Dot, Edge, Node

GRAPH_STYLE = {
    "bgcolor": "white",
    "graph_type": "graph",
    "nodesep": 0.2,
    "pad": "0.5, 0.5, 0, 0.5",
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
    def __init__(self, base_name):
        self._frame_count = 0
        self.base_name = base_name

    def graph_delete(self, topic, message):
        marks = MarkedNodes({message["node"]}, hue=0.9)
        self._write_image(graph_avl_tree(message["tree"], marked_nodes=marks))

    def graph_insert(self, topic, message):
        marks = MarkedNodes({message["node"]}, hue=0.4)
        self._write_image(graph_avl_tree(message["tree"], marked_nodes=marks))

    def graph_rebalanced(self, topic, message):
        root = message["root"]
        marks = MarkedNodes({root, root.left, root.right}, hue=0.6)
        self._write_image(graph_avl_tree(message["tree"], marked_nodes=marks))

    def graph_rotation(self, topic, message):
        marks = MarkedNodes(message["nodes"], hue=0.7)
        self._write_image(graph_avl_tree(message["tree"], marked_nodes=marks))

    def _write_image(self, graph):
        graph.write_png(f"{self.base_name}_{self._frame_count}.png")
        self._frame_count += 1


class MarkedNodes:
    def __init__(self, nodes, hue=0):
        self.nodes = nodes
        self.edge_color = self._create_color(hue, 0.2)
        self.fill_color = self._create_color(hue, 0.92)

    def __contains__(self, other):
        return other in self.nodes

    @staticmethod
    def _create_color(hue, lightness):
        rgb_color = (round(val * 255) for val in hls_to_rgb(hue, lightness, 1))
        return "#{:02x}{:02x}{:02x}".format(*rgb_color)


class TreeGrapher:
    def __init__(self, root, cache_size=256):
        if root is None:
            raise ValueError("Cannot graph an empty tree")
        self._height = self._cached_node_height(cache_size)
        self.root = root

    def create_graph(self, marked_nodes=None):
        graph = Dot(**GRAPH_STYLE)
        graph.set_edge_defaults(color="navy", penwidth=2)
        graph.set_node_defaults(**NODE_STYLE)
        marked_nodes = marked_nodes or set()
        self._draw_node(graph, self.root, marked_nodes)
        nodes = deque([self.root])
        while nodes:
            node = nodes.popleft()
            if node.left:
                self._draw_node(graph, node.left, marked_nodes, parent=node)
                nodes.append(node.left)
            self._draw_divider(graph, node)
            if node.right:
                self._draw_node(graph, node.right, marked_nodes, parent=node)
                nodes.append(node.right)
        return graph

    def _cached_node_height(self, cache_size):
        """Provides a node-height function to return the height of its subtree.

        The height is determined recursively by going down the entire subtree.
        This avoids suboptimal results in trees where balance factors have not
        been updated yet. A cache ensures that determining the height of all
        subtrees in the tree only takes time on the order of the node count.
        """

        @lru_cache(maxsize=cache_size)
        def height(node):
            if node is None:
                return -1
            return 1 + max(height(node.left), height(node.right))

        return height

    def _draw_divider(self, graph, node):
        """Draws a vertical divider to distinguish left/right child nodes."""
        marker_style = {"label": "", "width": 0, "height": 0, "style": "invis"}
        source = node.value
        for _ in range(self._height(node)):
            label = f":{source}"
            graph.add_node(Node(label, **marker_style))
            graph.add_edge(Edge(source, label, style="invis", weight=100))
            source = label

    def _draw_node(self, graph, node, marked_nodes, parent=None):
        """Draws actual node and edge up to parent, thick if imbalanced.

        Alternate colors for marked nodes are determined based on the fill or
        edge color specified by the `marked_nodes` object.
        """
        if node in marked_nodes:
            graph.add_node(Node(node.value, fillcolor=marked_nodes.fill_color))
        else:
            graph.add_node(Node(node.value))
        if parent is not None:
            style = {"penwidth": 4 if self._tallest_sibling(parent, node) else 2}
            if node in marked_nodes and parent in marked_nodes:
                style["color"] = marked_nodes.edge_color
            graph.add_edge(Edge(parent.value, node.value, **style))

    def _tallest_sibling(self, parent, node):
        """Returns whether the node is a taller subtree than its sibling."""
        if node is parent.left:
            return self._height(node) > self._height(parent.right)
        return self._height(node) > self._height(parent.left)


def graph_avl_tree(tree, marked_nodes=None):
    grapher = TreeGrapher(tree.root)
    return grapher.create_graph(marked_nodes=marked_nodes)
