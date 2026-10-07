"""Shared pytest fixtures for the Klystr test suite."""

import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def admin_api_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username='operator', password='operator', is_staff=True,
    )
    api_client.force_authenticate(user=user)
    return api_client
