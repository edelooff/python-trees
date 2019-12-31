from collections import deque
from colorsys import hls_to_rgb

from pydot import (
    Dot,
    Edge,
    Node)

GRAPH_STYLE = {
    'bgcolor': 'white',
    'graph_type': 'graph',
    'nodesep': 0.2,
    'pad': "0.5, 0.5, 0, 0.5"}
NODE_STYLE = {
    'fillcolor': 'lightyellow',
    'fontname': 'ubuntu mono bold',
    'fontsize': 18,
    'penwidth': 2,
    'shape': 'circle',
    'style': 'filled'}


class EventAnimator:
    def __init__(self, base_name):
        self._frame_count = 0
        self.base_name = base_name

    def graph_insert(self, topic, message):
        marks = MarkedNodes({message['node']}, hue=0.3)
        self._write_image(graph_avl_tree(message['tree'], marked_nodes=marks))

    def graph_rebalanced(self, topic, message):
        root = message['root']
        marks = MarkedNodes({root, root.left, root.right}, hue=0.6)
        self._write_image(graph_avl_tree(message['tree'], marked_nodes=marks))

    def graph_rotation(self, topic, message):
        marks = MarkedNodes(message['nodes'], hue=0.9)
        self._write_image(graph_avl_tree(message['tree'], marked_nodes=marks))

    def _write_image(self, graph):
        graph.write_png(f'{self.base_name}_{self._frame_count}.png')
        self._frame_count += 1


class MarkedNodes:
    def __init__(self, nodes, hue=0):
        self.nodes = nodes
        self.hue = hue

    def __contains__(self, other):
        return other in self.nodes

    @property
    def edge_color(self):
        rgb_color = (round(val * 255) for val in hls_to_rgb(self.hue, 0.2, 1))
        return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

    @property
    def fill_color(self):
        rgb_color = (round(val * 255) for val in hls_to_rgb(self.hue, 0.93, 1))
        return '#{:02x}{:02x}{:02x}'.format(*rgb_color)


def draw_marker(graph, node):
    """Draws an invisible marker node to separate left and right children."""
    source = node.value
    for _ in range(node_height(node)):
        label = f':{source}'
        graph.add_node(Node(label, label='', width=0, height=0, style='invis'))
        graph.add_edge(Edge(source, label, style='invis', weight=100))
        source = label


def draw_node(graph, node, marked_nodes):
    """Draws actual node and edge up to parent, thick if imbalanced.

    Alternate colors for marked nodes are determined based on the fill or edge
    color specified by the `marked_nodes` object.
    """
    if node in marked_nodes:
        graph.add_node(Node(node.value, fillcolor=marked_nodes.fill_color))
    else:
        graph.add_node(Node(node.value))
    if node.parent:
        style = {'penwidth': 4 if heavy_edge(node) else 2}
        if node in marked_nodes and node.parent in marked_nodes:
            style['color'] = marked_nodes.edge_color
        graph.add_edge(Edge(node.parent.value, node.value, **style))


def graph_avl_tree(tree, marked_nodes=None):
    graph = Dot(**GRAPH_STYLE)
    graph.set_edge_defaults(color='navy', penwidth=2)
    graph.set_node_defaults(**NODE_STYLE)
    marked_nodes = marked_nodes or set()
    if tree.root is not None:
        draw_node(graph, tree.root, marked_nodes)
        nodes = deque([tree.root])
        while nodes:
            node = nodes.popleft()
            if node.left:
                draw_node(graph, node.left, marked_nodes)
                nodes.append(node.left)
            if node.left or node.right:
                draw_marker(graph, node)
            if node.right:
                draw_node(graph, node.right, marked_nodes)
                nodes.append(node.right)
    return graph


def heavy_edge(node):
    """Returns whether the node is on a longer (heavier) branch of the tree.

    To account for edges on newly inserted nodes, where the parent's balance
    has not been updated, this function explicitly checks for 'only child'
    situations, in which case the edge is considered 'heavy'.
    """
    parent = node.parent
    if parent is not None:
        if node is parent.left:
            return parent.balance < 0 or parent.right is None
        return parent.balance > 0 or parent.left is None


def node_height(node):
    """Returns the height of the largest subtree under this node.

    This ensures that values are correctly sorted horizontally, at the cost of
    some horizontal space. The traversal algorithm prefers exploring the path
    that the balance factor leans towards, but otherwise will go left-first.
    This is to account for inaccurate balance factors during rebalancing.
    """
    height = -1
    while node:
        node = node.right if node.balance > 0 else (node.left or node.right)
        height += 1
    return height
