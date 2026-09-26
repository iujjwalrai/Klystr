"""Business logic for the nodes domain, kept out of views and models."""


from datetime import timedelta

from django.db import transaction
from django.utils import timezone


from .models import Node, NodeStatus

STALE_THRESHOLD = timedelta(seconds=40)


def register_node(*, name, cpu_capacity, memory_capacity, allocatable=None, labels=None):

    return Node.objects.create(
        name=name,
        status=NodeStatus.READY,
        cpu_capacity=cpu_capacity,
        memory_capacity=memory_capacity,
        allocable=allocatable or {},
        labels=labels or {},
        unschedulable=False,
        resource_version=1,
    )


@transaction.atomic
def record_heartbeat(node):
    node.last_heartbeat_at = timezone.now()

    if node.status==NodeStatus.NOT_READY:
        node.status = NodeStatus.READY
    
    node.resource_version += 1

    node.save(
        update_fields=["last_heartbeat_at", "status", "resource_version", "updated_at"]
    )

    return node

@transaction.atomic
def cordon(node):
    if node.status==NodeStatus.DRAINING:
        raise ValueError("Cannot cordon a node that is draining.")
    
    if node.unschedulable: return node
    node.unschedulable = True
    if node.status==NodeStatus.READY:
        node.status=NodeStatus.CORDONED
    
    node.resource_version += 1
    node.save(
        update_fields=["unschedulable", "status", "resource_version", "updated_at"]
    )  

    return node


@transaction.atomic
def uncordon(node):
    if node.status == NodeStatus.DRAINING:
        raise ValueError("Cannot uncordon a draining node.")

    if not node.unschedulable:
        return node

    node.unschedulable = False

    if node.status == NodeStatus.CORDONED:
        node.status = NodeStatus.READY

    node.resource_version += 1

    node.save(
        update_fields=[
            "unschedulable",
            "status",
            "resource_version",
            "updated_at",
        ]
    )

    return node


@transaction.atomic
def mark_stale_nodes():
    cutoff = timezone.now() - STALE_THRESHOLD

    nodes = list(
        Node.objects.filter(
            status=NodeStatus.READY,
            last_heartbeat_at__lt=cutoff,
        )
    )

    for node in nodes:
        node.status = NodeStatus.NOT_READY
        node.resource_version += 1

        node.save(
            update_fields=[
                "status",
                "resource_version",
                "updated_at",
            ]
        )

    return nodes


