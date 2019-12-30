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
