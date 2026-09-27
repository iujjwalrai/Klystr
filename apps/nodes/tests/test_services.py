"""Node lifecycle services: registration, heartbeats, cordon and staleness."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.nodes import services
from apps.nodes.models import Node
from apps.nodes.state import NodeStatus
from common.exceptions import InvalidSpec, InvalidTransition, ResourceConflict

pytestmark = pytest.mark.django_db


def make_node(name='node-1', **overrides):
    return services.register_node(name=name, cpu_capacity=2000, memory_capacity=4 * 1024**3, **overrides)


def age_heartbeat(node, by=services.STALE_THRESHOLD + timedelta(seconds=1)):
    Node.objects.filter(pk=node.pk).update(last_heartbeat_at=timezone.now() - by)


class TestRegister:
    def test_registers_ready_with_initial_heartbeat(self):
        node = make_node(allocatable={'cpu': 1800})

        assert node.status == NodeStatus.READY
        assert node.last_heartbeat_at is not None
        assert node.allocatable == {'cpu': 1800}
        assert node.is_schedulable

    @pytest.mark.parametrize('name', ['', 'Node-1', 'node_1', '-node', 'node-', 'a' * 64])
    def test_rejects_invalid_names(self, name):
        with pytest.raises(InvalidSpec) as exc_info:
            make_node(name=name)
        assert 'name' in exc_info.value.details['errors']

    def test_rejects_duplicate_name(self):
        make_node()
        with pytest.raises(InvalidSpec):
            make_node()


class TestHeartbeat:
    def test_does_not_bump_resource_version_when_ready(self):
        node = make_node()
        version = node.resource_version

        services.record_heartbeat(node)

        node.refresh_from_db()
        assert node.resource_version == version

    def test_recovers_not_ready_node(self):
        node = make_node()
        age_heartbeat(node)
        services.mark_stale_nodes()
        node.refresh_from_db()

        services.record_heartbeat(node)

        node.refresh_from_db()
        assert node.status == NodeStatus.READY

    def test_recovers_cordoned_node_back_to_cordoned(self):
        node = services.cordon(make_node())
        age_heartbeat(node)
        services.mark_stale_nodes()
        node.refresh_from_db()
        assert node.status == NodeStatus.NOT_READY

        services.record_heartbeat(node)

        node.refresh_from_db()
        assert node.status == NodeStatus.CORDONED
        assert node.unschedulable

    def test_heartbeat_does_not_conflict_with_later_edit(self):
        node = make_node()
        stale_copy = Node.objects.get(pk=node.pk)

        services.record_heartbeat(node)

        services.cordon(stale_copy)


class TestCordon:
    def test_cordon_and_uncordon(self):
        node = make_node()

        services.cordon(node)
        node.refresh_from_db()
        assert node.status == NodeStatus.CORDONED
        assert not node.is_schedulable

        services.uncordon(node)
        node.refresh_from_db()
        assert node.status == NodeStatus.READY
        assert node.is_schedulable

    def test_cordon_is_idempotent(self):
        node = services.cordon(make_node())
        version = node.resource_version

        services.cordon(node)

        assert node.resource_version == version

    @pytest.mark.parametrize('action', [services.cordon, services.uncordon])
    def test_draining_node_rejects_cordon_changes(self, action):
        node = make_node()
        Node.objects.filter(pk=node.pk).update(status=NodeStatus.DRAINING, unschedulable=True)
        node.refresh_from_db()

        with pytest.raises(InvalidTransition):
            action(node)

    def test_stale_copy_raises_conflict(self):
        node = make_node()
        stale_copy = Node.objects.get(pk=node.pk)
        services.cordon(node)
        services.uncordon(node)

        with pytest.raises(ResourceConflict):
            services.cordon(stale_copy)


class TestMarkStale:
    def test_marks_ready_and_cordoned_nodes(self):
        ready = make_node('ready')
        cordoned = services.cordon(make_node('cordoned'))
        fresh = make_node('fresh')
        age_heartbeat(ready)
        age_heartbeat(cordoned)

        marked = services.mark_stale_nodes()

        assert {n.name for n in marked} == {'ready', 'cordoned'}
        fresh.refresh_from_db()
        assert fresh.status == NodeStatus.READY

    def test_marks_node_that_never_heartbeated(self):
        node = make_node()
        Node.objects.filter(pk=node.pk).update(
            last_heartbeat_at=None,
            created_at=timezone.now() - services.STALE_THRESHOLD - timedelta(seconds=1),
        )

        assert [n.name for n in services.mark_stale_nodes()] == [node.name]

    def test_leaves_draining_nodes_alone(self):
        node = make_node()
        Node.objects.filter(pk=node.pk).update(status=NodeStatus.DRAINING)
        age_heartbeat(node)

        assert services.mark_stale_nodes() == []
