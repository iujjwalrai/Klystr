"""Sanity checks that the project wiring holds together."""

from django.urls import reverse


def test_healthz(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_all_apps_are_routed():
    for app in ('cluster', 'nodes', 'workloads', 'scheduler', 'controllers', 'agents'):
        __import__(f'apps.{app}.urls')


def test_admin_is_reachable():
    assert reverse('admin:index') == '/admin/'
