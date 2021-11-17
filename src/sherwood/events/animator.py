from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Pool
from multiprocessing.pool import Pool as PoolType
from operator import attrgetter
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
)

from ..renderers import Renderer, draw_tree
from ..trees.base import Tree
from ..typing import Comparable, Graft, Node
from .base import AnimationNode, Bus, Event


class Animator:
    def __init__(self, renderer: Renderer, base_name: str):
        self._frame_count = 0
        self.base_name = base_name
        self.renderer = renderer

    def graph_delete(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.node_set, marked_hue=0.95))

    def graph_delete_swap(self, event: Event) -> None:
        origin, swapped = event.nodes
        self._render(
            AnimationFrame(
                event.root,
                {swapped},
                marked_hue=0.95,
                extra_edges=[(origin, swapped)],
            )
        )

    def graph_insert(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.node_set, marked_hue=0.4))

    def graph_rebalanced(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.node_set, marked_hue=0.62))

    def graph_recolored(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.node_set, marked_hue=0.15))

    def graph_rotation(self, event: Event) -> None:
        self._render(AnimationFrame(event.root, event.node_set, marked_hue=0.83))

    def _render(self, frame: AnimationFrame) -> None:
        frame.render(self.frame_name, self.renderer)

    @property
    def frame_name(self) -> str:
        self._frame_count += 1
        return f"{self.base_name}_{self._frame_count}.png"

    @property
    def bus(self) -> Bus:
        """Returns a new Bus, subscribed to all supported animation events."""
        bus = Bus()
        bus.subscribe("delete", self.graph_delete)
        bus.subscribe("delete_swap", self.graph_delete_swap)
        bus.subscribe("insert", self.graph_insert)
        bus.subscribe("recolor", self.graph_recolored)
        bus.subscribe("rotate", self.graph_rotation)
        bus.subscribe("balanced", self.graph_rebalanced)
        return bus


class AsyncPoolAnimator(Animator):
    def __init__(self, renderer: Renderer, base_name: str, pool: PoolType):
        super().__init__(renderer, base_name)
        self.pool = pool

    def _render(self, frame: AnimationFrame) -> None:
        draw_args = frame.serialize(), self.frame_name, self.renderer
        self.pool.apply_async(self.draw_graph, draw_args)

    @staticmethod
    def draw_graph(serialized: SerialFrame, name: str, renderer: Renderer) -> None:
        """Multiprocess worker function to do the actual work of image rendering."""
        frame = AnimationFrame.from_serialized(serialized)
        frame.render(name, renderer)


@dataclass
class AnimationFrame:
    root: Node
    marked_nodes: Set[Node]
    marked_hue: float = 0
    extra_edges: List[Tuple[Node, Node]] = field(default_factory=list)

    @classmethod
    def from_serialized(cls, frame: SerialFrame) -> AnimationFrame:
        serialization = iter(frame.serialization)
        base = next(serialization)
        root = node = AnimationNode(base.value, options=base.options)
        node_map = {0: root}
        stack = []
        for index, graft in enumerate(serialization, 1):
            if graft.relative_branch == 0:
                stack.append(node)
                node.left = node = AnimationNode(graft.value, options=graft.options)
            else:
                for _ in range(1, graft.relative_branch):
                    node = stack.pop()
                node.right = node = AnimationNode(graft.value, options=graft.options)
            node_map[index] = node
        return cls(
            root=root,
            marked_nodes={node_map[index] for index in frame.marked_node_indices},
            marked_hue=frame.marked_node_hue,
            extra_edges=[(node_map[e1], node_map[e2]) for e1, e2, in frame.extra_edges],
        )

    def serialize(self) -> SerialFrame:
        serialization = list(dfs_branch_encoded(self.root))
        nodes = map(attrgetter("node"), serialization)
        index_map = {node: index for index, node in enumerate(nodes)}
        return SerialFrame(
            serialization=list(self._relative_serializer(serialization)),
            marked_node_indices=[index_map[node] for node in self.marked_nodes],
            marked_node_hue=self.marked_hue,
            extra_edges=[(index_map[e1], index_map[e2]) for e1, e2 in self.extra_edges],
        )

    def render(self, name: str, renderer: Renderer) -> None:
        graph = renderer(
            self.root,
            self.marked_nodes,
            self.marked_hue,
            self.extra_edges,
        )
        graph.write_png(name)

    @staticmethod
    def _relative_serializer(serialization: Iterable[Graft]) -> Iterator[SerialNode]:
        current = 0
        for abs_branch, node in serialization:
            relative_branch, current = 1 + current - abs_branch, abs_branch
            yield SerialNode(relative_branch, node.value, node_extra_values(node))


class SerialFrame(NamedTuple):
    serialization: List[SerialNode]
    marked_node_indices: List[int]
    marked_node_hue: float
    extra_edges: List[Tuple[int, int]]


class SerialNode(NamedTuple):
    relative_branch: int
    value: Comparable
    options: Dict[str, Any]


def dfs_branch_encoded(node: Optional[Node], branch: int = 0) -> Iterator[Graft]:
    if node is not None:
        yield Graft(branch, node)
        yield from dfs_branch_encoded(node.left, branch=branch + 1)
        yield from dfs_branch_encoded(node.right, branch=branch)


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
    """Context manager to create multiprocess animator, connected bus and tree."""
    with Pool() as pool:
        animator = AsyncPoolAnimator(renderer, base_name, pool)
        yield tree_type(event_bus=animator.bus)
        pool.close()
        pool.join()
