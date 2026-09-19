"""
Event bus interface.

The control plane publishes resource changes here; controllers, the
scheduler and any `watch` style API endpoints subscribe.
"""

import abc


class EventBus(abc.ABC):
    @abc.abstractmethod
    def publish(self, topic, event):
        """Publish a single event dict to `topic`."""

    @abc.abstractmethod
    def subscribe(self, *topics):
        """Yield events from `topics` until the caller stops iterating."""


class InMemoryBus(EventBus):
    """Single-process bus, useful in tests and for a single-node setup."""

    def __init__(self):
        self._subscribers = []

    def publish(self, topic, event):
        for topics, queue in self._subscribers:
            if topic in topics:
                queue.append((topic, event))

    def subscribe(self, *topics):
        queue = []
        self._subscribers.append((set(topics), queue))
        while True:
            if not queue:
                return
            yield queue.pop(0)
