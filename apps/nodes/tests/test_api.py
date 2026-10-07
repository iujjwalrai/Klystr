"""HTTP API for nodes."""

import pytest
from django.urls import reverse

from apps.nodes import services
from apps.nodes.models import Node
from apps.nodes.state import NodeStatus

pytestmark = pytest.mark.django_db

REGISTRATION = {'name': 'node-1', 'cpu_capacity': 2000, 'memory_capacity': 4 * 1024**3}


def list_url():
    return reverse('v1:nodes:node-list')


def detail_url(name, action=None):
    if action:
        return reverse(f'v1:nodes:node-{action}', kwargs={'name': name})
    return reverse('v1:nodes:node-detail', kwargs={'name': name})


@pytest.fixture
def node():
    return services.register_node(**REGISTRATION)


class TestPermissions:
    def test_anonymous_is_rejected(self, api_client):
        assert api_client.get(list_url()).status_code == 403

    def test_non_staff_can_read_but_not_write(self, api_client, django_user_model, node):
        user = django_user_model.objects.create_user(username='viewer', password='viewer')
        api_client.force_authenticate(user=user)

        assert api_client.get(detail_url(node.name)).status_code == 200
        assert api_client.post(detail_url(node.name, 'cordon')).status_code == 403


class TestRegisterAndRead:
    def test_register(self, admin_api_client):
        response = admin_api_client.post(list_url(), {**REGISTRATION, 'labels': {'zone': 'a'}}, format='json')

        assert response.status_code == 201
        body = response.json()
        assert body['name'] == 'node-1'
        assert body['status'] == NodeStatus.READY
        assert body['labels'] == {'zone': 'a'}
        assert body['last_heartbeat_at'] is not None

    def test_read_only_fields_are_ignored_on_register(self, admin_api_client):
        response = admin_api_client.post(
            list_url(), {**REGISTRATION, 'status': 'Draining', 'unschedulable': True}, format='json'
        )

        assert response.status_code == 201
        assert response.json()['status'] == NodeStatus.READY
        assert response.json()['unschedulable'] is False

    @pytest.mark.parametrize(
        'overrides',
        [{'name': 'Bad_Name'}, {'cpu_capacity': -1}, {'labels': {'zone': 1}}, {'allocatable': [1]}],
    )
    def test_register_rejects_invalid_input(self, admin_api_client, overrides):
        response = admin_api_client.post(list_url(), {**REGISTRATION, **overrides}, format='json')

        assert response.status_code == 400

    def test_duplicate_name_is_rejected(self, admin_api_client, node):
        response = admin_api_client.post(list_url(), REGISTRATION, format='json')

        assert response.status_code == 400

    def test_list_and_filter_by_status(self, admin_api_client, node):
        services.cordon(services.register_node(**{**REGISTRATION, 'name': 'node-2'}))

        all_nodes = admin_api_client.get(list_url()).json()
        ready = admin_api_client.get(list_url(), {'status': 'Ready'}).json()

        assert all_nodes['total'] == 2
        assert [n['name'] for n in ready['items']] == ['node-1']

    def test_unknown_status_filter_is_rejected(self, admin_api_client):
        response = admin_api_client.get(list_url(), {'status': 'Sleepy'})

        assert response.status_code == 400
        assert response.json()['reason'] == 'InvalidSpec'

    def test_retrieve_by_name(self, admin_api_client, node):
        response = admin_api_client.get(detail_url('node-1'))

        assert response.status_code == 200
        assert response.json()['id'] == node.id

    def test_missing_node_is_404(self, admin_api_client):
        assert admin_api_client.get(detail_url('nope')).status_code == 404


class TestUpdateAndDelete:
    def test_patch_labels(self, admin_api_client, node):
        response = admin_api_client.patch(detail_url(node.name), {'labels': {'zone': 'b'}}, format='json')

        assert response.status_code == 200
        assert response.json()['labels'] == {'zone': 'b'}
        assert response.json()['resource_version'] == node.resource_version + 1

    def test_patch_with_stale_resource_version_conflicts(self, admin_api_client, node):
        services.cordon(node)

        response = admin_api_client.patch(
            detail_url(node.name), {'labels': {'zone': 'b'}, 'resource_version': 1}, format='json'
        )

        assert response.status_code == 409
        assert response.json()['reason'] == 'Conflict'

    def test_patch_cannot_change_status(self, admin_api_client, node):
        response = admin_api_client.patch(detail_url(node.name), {'status': 'Draining'}, format='json')

        assert response.status_code == 200
        assert response.json()['status'] == NodeStatus.READY

    def test_put_is_not_allowed(self, admin_api_client, node):
        assert admin_api_client.put(detail_url(node.name), REGISTRATION, format='json').status_code == 405

    def test_delete(self, admin_api_client, node):
        assert admin_api_client.delete(detail_url(node.name)).status_code == 204
        assert not Node.objects.exists()


class TestActions:
    def test_cordon_and_uncordon(self, admin_api_client, node):
        cordoned = admin_api_client.post(detail_url(node.name, 'cordon')).json()
        assert cordoned['status'] == NodeStatus.CORDONED
        assert cordoned['unschedulable'] is True

        uncordoned = admin_api_client.post(detail_url(node.name, 'uncordon')).json()
        assert uncordoned['status'] == NodeStatus.READY
        assert uncordoned['unschedulable'] is False

    def test_cordon_draining_node_is_conflict(self, admin_api_client, node):
        Node.objects.filter(pk=node.pk).update(status=NodeStatus.DRAINING)

        response = admin_api_client.post(detail_url(node.name, 'cordon'))

        assert response.status_code == 409
        assert response.json()['reason'] == 'InvalidTransition'

    def test_heartbeat(self, admin_api_client, node):
        before = node.last_heartbeat_at

        response = admin_api_client.post(detail_url(node.name, 'heartbeat'))

        assert response.status_code == 200
        node.refresh_from_db()
        assert node.last_heartbeat_at > before
