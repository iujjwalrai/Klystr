"""Node readiness conditions."""

from django.db import models


class NodeStatus(models.TextChoices):
    READY = 'Ready', 'Ready'
    NOT_READY = 'NotReady', 'NotReady'
    CORDONED = 'Cordoned', 'Cordoned'
    DRAINING = 'Draining', 'Draining'
    UNKNOWN = 'Unknown', 'Unknown'


SCHEDULABLE_STATUSES = frozenset({NodeStatus.READY})
