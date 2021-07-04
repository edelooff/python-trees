from .base import Renderer, TreeRenderer
from .properties import (
    color_marked_node_edge,
    imbalanced_edge_weight,
    outline_marked_node,
    red_black_node_color,
)

draw_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge],
    node_attr_funcs=[outline_marked_node],
)

draw_avl_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge, imbalanced_edge_weight],
    node_attr_funcs=[outline_marked_node],
)

draw_redblack_tree: Renderer = TreeRenderer(
    edge_attr_funcs=[color_marked_node_edge],
    node_attr_funcs=[outline_marked_node, red_black_node_color],
)


__all__ = "Renderer", "draw_tree", "draw_avl_tree", "draw_redblack_tree"
