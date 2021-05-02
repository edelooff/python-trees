from __future__ import annotations

from typing import Callable, Dict, NamedTuple, Set

from ..trees.base import Node


class Event(NamedTuple):
    root: Node
    nodes: Set[Node]


EventHandler = Callable[[str, Event], None]


class Bus:
    """A trivial pub/sub model to allow observation of tree internals."""

    def __init__(self) -> None:
        self.subscribers: Dict[str, Set[EventHandler]] = {}

    def publish(self, topic: str, event: Event) -> None:
        full_topic = topic
        while topic:
            for handler in self.subscribers.get(topic, ()):
                handler(full_topic, event)
            topic, _, _ = topic.rpartition(".")

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self.subscribers.setdefault(topic, set()).add(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        for handlers in self.subscribers.values():
            handlers.discard(handler)
