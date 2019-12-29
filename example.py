import random

from avl import AVLTree
from grapher import graph_avl_tree


def main():
    tree = AVLTree()
    numbers = random.sample(range(100), 32)
    for index, num in enumerate(numbers):
        print(f'INSERTING {num} INTO TREE')
        tree.insert(num)
        graph = graph_avl_tree(tree)
        graph.write_png(f'tree_{index}.png')


if __name__ == '__main__':
    main()
