import random

from sherwood.events import tree_renderer
from sherwood.renderers import draw_avl_tree, draw_redblack_tree
from sherwood.trees import AVLTree, RedBlackTree


def main():
    example_values = [43, 81, 95, 16, 28, 23, 86]
    with tree_renderer(AVLTree, "avl-example", renderer=draw_avl_tree) as tree:
        for value in example_values:
            tree.insert(value)
        tree.delete(28)

    with tree_renderer(RedBlackTree, "rb-example", renderer=draw_redblack_tree) as tree:
        for value in example_values:
            tree.insert(value)
        tree.delete(81)

    insert_sample = random.sample(range(100, 1000), 24)
    with tree_renderer(AVLTree, "avl-inserts", renderer=draw_avl_tree) as tree:
        for value in insert_sample:
            tree.insert(value)

    with tree_renderer(RedBlackTree, "rb-inserts", renderer=draw_redblack_tree) as tree:
        for value in insert_sample:
            tree.insert(value)

    with tree_renderer(RedBlackTree, "rb-recolor", renderer=draw_redblack_tree) as tree:
        for value in [13, 16, 8, 17, 15, 11, 5, 14]:
            tree.insert(value)
        tree.delete(14)
        for value in [12, 10, 6, 3, 9]:
            tree.insert(value)
        tree.delete(9)
        for value in [4, 2, 1]:
            tree.insert(value)


if __name__ == "__main__":
    main()
