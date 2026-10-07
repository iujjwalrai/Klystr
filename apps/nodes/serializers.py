"""Request/response serializers for the nodes API."""

from rest_framework import serializers

from .models import Node


def _validate_labels(value):
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        raise serializers.ValidationError('Labels must be an object of string keys to string values.')
    return value


def _validate_allocatable(value):
    if not isinstance(value, dict):
        raise serializers.ValidationError('Allocatable must be an object.')
    return value


class NodeSerializer(serializers.ModelSerializer):
    """Full node representation; also used to register a node."""

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
            'unschedulable',
            'resource_version',
            'last_heartbeat_at',
            'created_at',
            'updated_at',
        ]

    def validate_labels(self, value):
        return _validate_labels(value)

    def validate_allocatable(self, value):
        return _validate_allocatable(value)


class NodeUpdateSerializer(serializers.ModelSerializer):
    """
    Partial update of a node's mutable fields.

    `resource_version` is optional; when sent, the update only applies if the
    node has not changed since that version.
    """

    resource_version = serializers.IntegerField(required=False, min_value=1)

    class Meta:
        model = Node
        fields = ['labels', 'allocatable', 'cpu_capacity', 'memory_capacity', 'resource_version']

    def validate_labels(self, value):
        return _validate_labels(value)

    def validate_allocatable(self, value):
        return _validate_allocatable(value)
