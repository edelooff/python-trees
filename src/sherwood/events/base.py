from __future__ import annotations

from typing import Callable, Dict, NamedTuple, Set

from ..trees.base import Node


class Event(NamedTuple):
    root: Node
    nodes: Set[Node]


class Bus:
    """A trivial pub/sub model to allow observation of tree internals."""

    def __init__(self):
        self.subscribers: Dict[str, Callable[str, Event], None] = {}

    def publish(self, topic: str, event: Event) -> None:
        full_topic = topic
        while topic:
            for handler in self.subscribers.get(topic, ()):
                handler(full_topic, event)
            topic, _, _ = topic.rpartition(".")

    def subscribe(self, topic, handler=None):
        def _wrapper(handler):
            self.subscribers.setdefault(topic, set()).add(handler)
            return handler

        return _wrapper if handler is None else _wrapper(handler)

    def unsubscribe(self, handler):
        for handlers in self.subscribers.values():
            handlers.discard(handler)
