"""The node-lifecycle control loop."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.controllers.management.commands.run_worker import WORKERS
from apps.nodes import services
from apps.nodes.models import Node
from apps.nodes.state import NodeStatus
from workers.tasks.node_lifecycle import NodeLifecycleWorker


def test_worker_is_registered():
    assert WORKERS['node-lifecycle'] is NodeLifecycleWorker


def test_unknown_worker_is_rejected():
    with pytest.raises(CommandError):
        call_command('run_worker', 'nope')


@pytest.mark.django_db
def test_reconcile_marks_stale_nodes():
    stale = services.register_node(name='stale', cpu_capacity=1000, memory_capacity=1024**3)
    services.register_node(name='fresh', cpu_capacity=1000, memory_capacity=1024**3)
    Node.objects.filter(pk=stale.pk).update(
        last_heartbeat_at=timezone.now() - services.stale_threshold() - timedelta(seconds=1)
    )

    marked = NodeLifecycleWorker().reconcile()

    assert [n.name for n in marked] == ['stale']
    assert Node.objects.get(name='stale').status == NodeStatus.NOT_READY
    assert Node.objects.get(name='fresh').status == NodeStatus.READY
