from collections import deque

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


def draw_marker(graph, node):
    """Draws an invisible marker node to separate left and right children."""
    source = node.value
    for _ in range(node_height(node)):
        label = f':{source}'
        graph.add_node(Node(label, label='', width=0, height=0, style='invis'))
        graph.add_edge(Edge(source, label, style='invis', weight=100))
        source = label


def draw_node(graph, node):
    """Draws actual node and edge up to parent, thick if imbalanced."""
    graph.add_node(Node(node.value))
    if node.parent:
        penwidth = 4 if heavy_edge(node) else 2
        graph.add_edge(Edge(node.parent.value, node.value, penwidth=penwidth))


def graph_avl_tree(tree):
    graph = Dot(**GRAPH_STYLE)
    graph.set_edge_defaults(color='navy', penwidth=2)
    graph.set_node_defaults(**NODE_STYLE)
    if tree.root is not None:
        draw_node(graph, tree.root)
        nodes = deque([tree.root])
        while nodes:
            node = nodes.popleft()
            if node.left:
                draw_node(graph, node.left)
                nodes.append(node.left)
            if node.left or node.right:
                draw_marker(graph, node)
            if node.right:
                draw_node(graph, node.right)
                nodes.append(node.right)
    return graph


def heavy_edge(node):
    if node.parent is not None:
        heavy_edge_balance = -1 if node.parent.left is node else 1
        return node.parent.balance == heavy_edge_balance


def node_height(node):
    height = -1
    while node:
        node = node.right if node.balance > 0 else node.left
        height += 1
    return height
