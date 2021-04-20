import random
from contextlib import contextmanager

from avl import AVLTree, EventBus
from grapher import EventAnimator


@contextmanager
def fully_graphed_tree(base_name):
    event_bus = EventBus()
    animator = EventAnimator(base_name)
    event_bus.subscribe("delete", animator.graph_delete)
    event_bus.subscribe("insert", animator.graph_insert)
    event_bus.subscribe("rotate", animator.graph_rotation)
    event_bus.subscribe("balanced", animator.graph_rebalanced)
    yield AVLTree(event_bus=event_bus)
    animator.finish()


def main():
    with fully_graphed_tree("example") as tree:
        tree.bulk_insert([43, 81, 95, 16, 28, 23, 63, 57])
        tree.delete(16)

    with fully_graphed_tree("balanced_inserts") as tree:
        tree.bulk_insert(random.sample(range(100, 1000), 32))


if __name__ == "__main__":
    main()
