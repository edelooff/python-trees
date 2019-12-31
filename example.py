import random

from avl import (
    AVLTree,
    EventBus)
from grapher import EventAnimator


def fully_graphed_tree(base_name):
    event_bus = EventBus()
    animator = EventAnimator(base_name)
    event_bus.subscribe('insert', animator.graph_insert)
    event_bus.subscribe('rotate', animator.graph_rotation)
    event_bus.subscribe('balanced', animator.graph_rebalanced)
    return AVLTree(event_bus=event_bus)


def main():
    tree = fully_graphed_tree('balanced_inserts')
    for num in random.sample(range(100, 1000), 32):
        tree.insert(num)


if __name__ == '__main__':
    main()
