import random

from sherwood.events.animator import tree_renderer
from sherwood.trees.avl import AVLTree


def main():
    with tree_renderer(AVLTree, "example") as tree:
        for value in [43, 81, 95, 16, 28, 23, 63, 57]:
            tree.insert(value)
        tree.delete(16)

    with tree_renderer(AVLTree, "balanced_inserts") as tree:
        for value in random.sample(range(100, 1000), 32):
            tree.insert(value)


if __name__ == "__main__":
    main()
