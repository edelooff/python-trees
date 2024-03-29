from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Sequence, Set, final

from ..trees.base import BinaryNode
from ..typing import Node


@final
@dataclass(eq=False)
class AnimationNode(BinaryNode):
    left: Optional[AnimationNode] = None
    right: Optional[AnimationNode] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    topic: str
    root: Node
    nodes: Sequence[Node]

    @property
    def node_set(self):
        return set(self.nodes)


EventHandler = Callable[[Event], None]


class Bus:
    """A trivial pub/sub model to allow observation of tree internals."""

    def __init__(self) -> None:
        self.subscribers: Dict[str, Set[EventHandler]] = {}

    def publish(self, topic: str, root: Node, nodes: Sequence[Node]) -> None:
        event = Event(topic=topic, root=root, nodes=nodes)
        while topic:
            for handler in self.subscribers.get(topic, ()):
                handler(event)
            topic, _, _ = topic.rpartition(".")

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self.subscribers.setdefault(topic, set()).add(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        for handlers in self.subscribers.values():
            handlers.discard(handler)
