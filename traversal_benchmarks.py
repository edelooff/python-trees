"""Compares ordered-traversal functions

This compares the different depth-first in-order traversers, as well as
post-traversal sorted breadth-first traversal.
"""

import timeit

from avl import AVLTree
from traversal import breadth_first, depth_first_inorder, ordered_iterative

ORDERED_TRAVERSERS = [
    ("iterative", lambda tree: lambda: list(ordered_iterative(tree))),
    ("recursive", lambda tree: lambda: list(depth_first_inorder(tree))),
    ("sorted-bfs", lambda tree: lambda: sorted(breadth_first(tree))),
]


def main():
    for tree_size in (100, 1000, 10000):
        tree = AVLTree(range(tree_size))
        print(f"Ordered traversal of a tree size {tree_size}")
        for name, test_func_creator in ORDERED_TRAVERSERS:
            test_func = test_func_creator(tree)
            assert test_func() == sorted(range(tree_size))
            best = min(timeit.repeat(test_func, number=1000, repeat=3))
            print(f"  * [{name}]: {best * 1000:.1f}μs")


if __name__ == "__main__":
    main()
