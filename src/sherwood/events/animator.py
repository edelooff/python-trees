from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from multiprocessing import Pool
from types import TracebackType
from typing import Any, Iterator, List, NamedTuple, Optional, Set, Tuple, Type, Union

from ..trees.base import BinaryNode, Node, Tree
from ..utils.draw import MarkedNodes, tree_graph
from .base import Bus, Event


class Animator:
    def __init__(self, base_name: str):
        self._frame_count = 0
        self.base_name = base_name
        self.workers = Pool()

    def graph_delete(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.9))

    def graph_insert(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.4))

    def graph_rebalanced(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.6))

    def graph_rotation(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, highlight_hue=0.7))

    def _render(self, frame: AnimationFrame) -> None:
        self.workers.apply_async(self.draw_graph, (frame.serialize(), self.frame_name))

    @property
    def frame_name(self) -> str:
        self._frame_count += 1
        return f"{self.base_name}_{self._frame_count}.png"

    def finish(self) -> None:
        """Closes the worker pool for additional jobs and waits for them to finish."""
        self.workers.close()
        self.workers.join()

    @staticmethod
    def draw_graph(serialized_frame: SerialFrame, name: str) -> None:
        """Multiprocess worker function to do the actual work of image rendering."""
        frame = AnimationFrame.from_serialized(serialized_frame)
        frame.render(name)

    def __enter__(self) -> Bus:
        bus = Bus()
        bus.subscribe("delete", self.graph_delete)
        bus.subscribe("insert", self.graph_insert)
        bus.subscribe("rotate", self.graph_rotation)
        bus.subscribe("balanced", self.graph_rebalanced)
        return bus

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_value: Optional[Exception],
        traceback: Optional[TracebackType],
    ) -> None:
        self.finish()


@dataclass
class AnimationFrame:
    root: Node
    highlighted_nodes: Set[Node]
    highlight_hue: float = 0

    @classmethod
    def from_serialized(cls, frame: SerialFrame) -> AnimationFrame:
        ivalues = iter(frame.serialization)
        root = node = BinaryNode(next(ivalues))
        marked_nodes: Set[Node] = {root} if 0 in frame.node_indices else set()
        stack = []
        for idx, (branch_id, value) in enumerate(zip(ivalues, ivalues), 1):
            if branch_id == 0:
                stack.append(node)
                node.left = node = BinaryNode(value)
            else:
                for _ in range(1, branch_id):
                    node = stack.pop()
                node.right = node = BinaryNode(value)
            if idx in frame.node_indices:
                marked_nodes.add(node)
        return cls(root, marked_nodes, frame.hue)

    def serialize(self) -> SerialFrame:
        serialization: List[Any] = []
        node_indices: List[int] = []
        cur_branch = 0
        for node_index, (node, new_branch) in enumerate(dfs_branch_encoded(self.root)):
            if node in self.marked_nodes:
                node_indices.append(node_index)
            change, cur_branch = 1 + cur_branch - new_branch, new_branch
            serialization.append(change)
            serialization.append(node.value)
        return SerialFrame(serialization[1:], node_indices, self.highlight_hue)

    @property
    def marked_nodes(self) -> MarkedNodes:
        return MarkedNodes(self.highlighted_nodes, hue=self.highlight_hue)

    def render(self, name: str) -> None:
        graph = tree_graph(self.root, marked_nodes=self.marked_nodes)
        graph.write_png(name)


class SerialFrame(NamedTuple):
    serialization: List[Union[Any, int]]
    node_indices: List[int]
    hue: float


def dfs_branch_encoded(
    node: Optional[Node], branch_id: int = 0
) -> Iterator[Tuple[Node, int]]:
    if node is not None:
        yield node, branch_id
        yield from dfs_branch_encoded(node.left, branch_id=branch_id + 1)
        yield from dfs_branch_encoded(node.right, branch_id=branch_id)


@contextmanager
def tree_renderer(tree_type: Type[Tree], base_name: str) -> Iterator[Tree]:
    animator = Animator(base_name)
    with animator as bus:
        yield tree_type(event_bus=bus)
