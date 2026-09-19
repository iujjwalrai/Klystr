"""
Container runtime abstraction.

Node agents talk to a runtime through this interface so the rest of the
control plane never depends on Docker specifically.
"""

import abc


class ContainerRuntime(abc.ABC):
    """Minimal surface the agent needs to run and observe containers."""

    @abc.abstractmethod
    def create(self, name, image, command=None, env=None, limits=None):
        """Create a container and return its runtime id."""

    @abc.abstractmethod
    def start(self, container_id):
        """Start a created container."""

    @abc.abstractmethod
    def stop(self, container_id, timeout=10):
        """Stop a running container, SIGKILL after `timeout` seconds."""

    @abc.abstractmethod
    def remove(self, container_id, force=False):
        """Delete a container and its writable layer."""

    @abc.abstractmethod
    def inspect(self, container_id):
        """Return current state: exit code, started/finished timestamps."""

    @abc.abstractmethod
    def logs(self, container_id, tail=100):
        """Return the most recent log lines."""

    @abc.abstractmethod
    def list(self, label_selector=None):
        """List containers managed by this node agent."""
