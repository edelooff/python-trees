from typing import Any

from ..events.base import AnimationNode
from ..trees.base import Node
from ..trees.redblack import RBNode
from .base import DotAttrs, DrawContext


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
