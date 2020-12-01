from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import count
from random import seed, shuffle
from timeit import timeit
from typing import Any, Optional

from traversal import depth_first_inorder, depth_first_preorder


@dataclass
class Node:
    value: Any
    left: Optional[Node] = None
    right: Optional[Node] = None


class Tree:
    def __init__(self, *values):
        self.root = None
        for value in values:
            self.insert(value)

    def __eq__(self, other):
        if not isinstance(other, Tree):
            return False
        return self.root == other.root

    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
            return self.root

        node = self.root
        while True:
            if value == node.value:
                raise ValueError(f"duplicate value {value}")
            elif value < node.value:
                if node.left is not None:
                    node = node.left
                    continue
                node.left = new = Node(value)
            else:
                if node.right is not None:
                    node = node.right
                    continue
                node.right = new = Node(value)
            return new


def construct_from_preorder(values):
    ivalues = iter(values)
    root = node = Node(next(ivalues))
    stack = deque([root])
    for value in ivalues:
        if value < node.value:
            node.left = node = Node(value)
            stack.appendleft(node)
        else:
            while stack and value > stack[0].value:
                node = stack.popleft()
            node.right = node = Node(value)
            stack.appendleft(node)
    return root


def construct_from_preorder_inorder(pre_order, in_order):
    # print(f"\nStack recreating tree from PO {pre_order} and IO {in_order}")
    pre_iter = iter(pre_order)
    root = node = Node(next(pre_iter))
    stack = deque([node])
    right = False

    for ivalue in in_order:
        # print(f"\nProcessing in-order value {ivalue}, stack: {stack}")
        if stack and ivalue == stack[0].value:
            node = stack.popleft()
            right = True
            # print(f"- on top of in stack, going up tp {node}!")
            continue
        for pvalue in pre_iter:
            if right:
                # print(f"- appending {pvalue} to right of {node}")
                node.right = node = Node(pvalue)
            else:
                # print(f"- appending {pvalue} to left of {node}")
                node.left = node = Node(pvalue)
            if right := pvalue == ivalue:
                break
            stack.appendleft(node)
    return root


def preorder_permutation_generator(preorder):
    """Generates different structural permutations for a single preorder sequence."""
    root, *additional = map(Node, preorder)

    def _constructor(root, nodes):
        if not nodes:
            yield root
            return
        cursor = root
        while True:
            while cursor.right is not None:
                cursor = cursor.right
            cursor.right = nodes[0]
            yield from _constructor(root, nodes[1:])
            cursor.right = None
            if cursor.left is None:
                cursor.left = nodes[0]
                yield from _constructor(root, nodes[1:])
                cursor.left = None
                return
            cursor = cursor.left

    return _constructor(root, additional)


def main():
    seed(1)
    dfsio = depth_first_inorder
    dfspo = depth_first_preorder
    numbers = list(range(128))
    for attempt in count(1):
        shuffle(numbers)
        tree = Tree(*numbers)
        for algo in [construct_from_preorder]:
            retree = algo(dfspo(tree))
            assert tree.root == retree
            treetime = timeit(lambda: algo(dfspo(tree)), number=5000)
            print(algo.__name__, treetime)

        for algo in [construct_from_preorder_inorder]:
            retree = algo(dfspo(tree), dfsio(tree))
            assert tree.root == retree
            treetime = timeit(lambda: algo(dfspo(tree), dfsio(tree)), number=5000)
            print(algo.__name__, treetime)
        print("")
        if attempt % 1000 == 0:
            print(f"{attempt} reconstructions without failure")


if __name__ == "__main__":
    main()
