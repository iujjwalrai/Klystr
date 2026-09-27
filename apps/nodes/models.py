from django.core.exceptions import ValidationError
from django.db import models

from .state import SCHEDULABLE_STATUSES, NodeStatus

NAME_MAX_LENGTH = 63
NAME_ALLOWED_CHARS = frozenset('abcdefghijklmnopqrstuvwxyz0123456789-')


def is_valid_name(value):
    """Node names are DNS-1123 labels: lowercase alphanumerics and '-', alphanumeric at both ends."""
    if not value:
        raise ValidationError('Name cannot be empty.')

    if len(value) > NAME_MAX_LENGTH:
        raise ValidationError(f'Name cannot be longer than {NAME_MAX_LENGTH} characters.')

    if any(char not in NAME_ALLOWED_CHARS for char in value):
        raise ValidationError('Node name can only contain lowercase alphanumeric characters and hyphens.')

    if value.startswith('-') or value.endswith('-'):
        raise ValidationError('Node name cannot start or end with a hyphen.')


class Node(models.Model):
    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=[is_valid_name],
    )

    status = models.CharField(
        max_length=10,
        choices=NodeStatus.choices,
        default=NodeStatus.NOT_READY,
    )

    cpu_capacity = models.PositiveIntegerField(
        help_text='CPU capacity in millicores (m). For example, 1000m = 1 CPU core.'
    )

    memory_capacity = models.PositiveBigIntegerField(
        help_text='Memory capacity in bytes. For example, 1073741824 bytes = 1 GiB.'
    )

    allocatable = models.JSONField(
        default=dict,
        blank=True,
    )

    labels = models.JSONField(
        default=dict,
        blank=True,
    )

    unschedulable = models.BooleanField(
        default=False,
    )

    last_heartbeat_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resource_version = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_schedulable(self):
        return self.status in SCHEDULABLE_STATUSES and not self.unschedulable
