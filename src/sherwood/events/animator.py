from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from multiprocessing import Pool
from types import TracebackType
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Set, Tuple, Type

from ..trees.base import Node, Tree
from ..renderers import Renderer, draw_tree
from .base import AnimationNode, Bus, Event


class Animator:
    def __init__(self, renderer: Renderer, base_name: str):
        self._frame_count = 0
        self.base_name = base_name
        self.renderer = renderer
        self.workers = Pool()

    def graph_delete(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, marked_hue=0.95))

    def graph_insert(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, marked_hue=0.4))

    def graph_rebalanced(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, marked_hue=0.62))

    def graph_rotation(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.nodes, marked_hue=0.83))

    def _render(self, frame: AnimationFrame) -> None:
        draw_args = frame.serialize(), self.frame_name, self.renderer
        self.workers.apply_async(self.draw_graph, draw_args)

    @property
    def frame_name(self) -> str:
        self._frame_count += 1
        return f"{self.base_name}_{self._frame_count}.png"

    def finish(self) -> None:
        """Closes the worker pool for additional jobs and waits for them to finish."""
        self.workers.close()
        self.workers.join()

    @staticmethod
    def draw_graph(serialized: SerialFrame, name: str, renderer: Renderer) -> None:
        """Multiprocess worker function to do the actual work of image rendering."""
        frame = AnimationFrame.from_serialized(serialized)
        frame.render(name, renderer)

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
    marked: Set[Node]
    marked_hue: float = 0

    @classmethod
    def from_serialized(cls, frame: SerialFrame) -> AnimationFrame:
        serialization = iter(frame.serialization)
        _branch, root_value, root_options = next(serialization)
        root = node = AnimationNode(root_value, options=root_options)
        marked: Set[Node] = {root} if 0 in frame.node_indices else set()
        stack = []
        for idx, (branch_id, value, options) in enumerate(serialization, 1):
            if branch_id == 0:
                stack.append(node)
                node.left = node = AnimationNode(value, options=options)
            else:
                for _ in range(1, branch_id):
                    node = stack.pop()
                node.right = node = AnimationNode(value, options=options)
            if idx in frame.node_indices:
                marked.add(node)
        return cls(root, marked, frame.hue)

    def serialize(self) -> SerialFrame:
        serialization: List[Any] = []
        node_indices: List[int] = []
        cur_branch = 0
        for node_index, (node, new_branch) in enumerate(dfs_branch_encoded(self.root)):
            if node in self.marked:
                node_indices.append(node_index)
            change, cur_branch = 1 + cur_branch - new_branch, new_branch
            serialization.append((change, node.value, node_extra_values(node)))
        return SerialFrame(serialization, node_indices, self.marked_hue)

    def render(self, name: str, renderer: Renderer) -> None:
        graph = renderer(self.root, self.marked, self.marked_hue)
        graph.write_png(name)


class SerialFrame(NamedTuple):
    serialization: List[Tuple[int, Any, Dict[str, Any]]]
    node_indices: List[int]
    hue: float


def dfs_branch_encoded(
    node: Optional[Node], branch_id: int = 0
) -> Iterator[Tuple[Node, int]]:
    if node is not None:
        yield node, branch_id
        yield from dfs_branch_encoded(node.left, branch_id=branch_id + 1)
        yield from dfs_branch_encoded(node.right, branch_id=branch_id)


def node_extra_values(node: Node) -> Dict[str, Any]:
    def node_attrs() -> Iterator[Tuple[str, Any]]:
        for attr, value in vars(node).items():
            if attr in {"value", "left", "right"}:
                continue
            if isinstance(value, Enum):
                value = value.name
            yield attr, value

    return dict(node_attrs())


@contextmanager
def tree_renderer(
    tree_type: Type[Tree], base_name: str, renderer: Renderer = draw_tree
) -> Iterator[Tree]:
    animator = Animator(renderer, base_name)
    with animator as bus:
        yield tree_type(event_bus=bus)
