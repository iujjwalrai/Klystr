"""Request/response serializers for the nodes API."""

from rest_framework import serializers  # noqa: F401

from .models import Node


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            'id',
            'name',
            'status',
            'cpu_capacity',
            'memory_capacity',
            'allocatable',
            'labels',
            'unschedulable',
            'resource_version',
            'last_heartbeat_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'resource_version',
            'last_heartbeat_at',
            'created_at',
            'updated_at',
        ]
