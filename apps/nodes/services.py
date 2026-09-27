"""Business logic for the nodes domain, kept out of views and models."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils import timezone

from common.exceptions import InvalidSpec, InvalidTransition, ResourceConflict

from .models import Node
from .state import NodeStatus

STALE_THRESHOLD = timedelta(seconds=40)

# Statuses a node leaves when its heartbeats stop. Draining is left alone so an
# in-progress drain is not forgotten; the drain logic owns that state.
STALEABLE_STATUSES = frozenset({NodeStatus.READY, NodeStatus.CORDONED})


def _save_versioned(node, **changes):
    """
    Apply `changes` only if nobody has modified `node` since it was read.

    Bumps resource_version and raises ResourceConflict when the stored version
    no longer matches the one on `node`.
    """
    now = timezone.now()
    updated = Node.objects.filter(pk=node.pk, resource_version=node.resource_version).update(
        resource_version=F('resource_version') + 1,
        updated_at=now,
        **changes,
    )
    if not updated:
        raise ResourceConflict(
            f'Node {node.name!r} was modified concurrently; re-read it and retry.',
            name=node.name,
            resource_version=node.resource_version,
        )

    for field, value in changes.items():
        setattr(node, field, value)
    node.resource_version += 1
    node.updated_at = now
    return node


def _ready_status(node):
    """The status a node returns to once it is healthy again."""
    return NodeStatus.CORDONED if node.unschedulable else NodeStatus.READY


def register_node(*, name, cpu_capacity, memory_capacity, allocatable=None, labels=None):
    node = Node(
        name=name,
        status=NodeStatus.READY,
        cpu_capacity=cpu_capacity,
        memory_capacity=memory_capacity,
        allocatable=allocatable or {},
        labels=labels or {},
        unschedulable=False,
        # Registration comes from a live agent, so it counts as the first heartbeat.
        last_heartbeat_at=timezone.now(),
        resource_version=1,
    )
    try:
        node.full_clean()
    except ValidationError as exc:
        raise InvalidSpec('Invalid node registration.', errors=exc.message_dict) from exc

    node.save()
    return node


def record_heartbeat(node):
    """
    Record that the node's agent is alive.

    The heartbeat timestamp alone does not bump resource_version, so frequent
    heartbeats never conflict with user edits. Only a status change does.
    """
    now = timezone.now()
    Node.objects.filter(pk=node.pk).update(last_heartbeat_at=now)
    node.last_heartbeat_at = now

    if node.status == NodeStatus.NOT_READY:
        node.refresh_from_db()
        if node.status == NodeStatus.NOT_READY:
            _save_versioned(node, status=_ready_status(node))

    return node


def cordon(node):
    if node.status == NodeStatus.DRAINING:
        raise InvalidTransition('Cannot cordon a node that is draining.', name=node.name)

    if node.unschedulable:
        return node

    changes = {'unschedulable': True}
    if node.status == NodeStatus.READY:
        changes['status'] = NodeStatus.CORDONED

    return _save_versioned(node, **changes)


def uncordon(node):
    if node.status == NodeStatus.DRAINING:
        raise InvalidTransition('Cannot uncordon a draining node.', name=node.name)

    if not node.unschedulable:
        return node

    changes = {'unschedulable': False}
    if node.status == NodeStatus.CORDONED:
        changes['status'] = NodeStatus.READY

    return _save_versioned(node, **changes)


def mark_stale_nodes():
    """Mark nodes NotReady when their agent has stopped heartbeating. Returns the nodes marked."""
    cutoff = timezone.now() - STALE_THRESHOLD
    stale = Q(last_heartbeat_at__lt=cutoff) | Q(last_heartbeat_at__isnull=True, created_at__lt=cutoff)

    marked = []
    for node in Node.objects.filter(stale, status__in=STALEABLE_STATUSES):
        # Re-check staleness in the UPDATE itself, so a heartbeat that lands
        # between the read and the write keeps the node Ready.
        updated = Node.objects.filter(stale, pk=node.pk, resource_version=node.resource_version).update(
            status=NodeStatus.NOT_READY,
            resource_version=F('resource_version') + 1,
            updated_at=timezone.now(),
        )
        if updated:
            node.refresh_from_db()
            marked.append(node)

    return marked
