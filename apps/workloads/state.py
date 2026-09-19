"""Workload and pod lifecycle phases."""

from django.db import models


class Phase(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    SCHEDULED = 'Scheduled', 'Scheduled'
    RUNNING = 'Running', 'Running'
    SUCCEEDED = 'Succeeded', 'Succeeded'
    FAILED = 'Failed', 'Failed'
    TERMINATING = 'Terminating', 'Terminating'


TERMINAL_PHASES = frozenset({Phase.SUCCEEDED, Phase.FAILED})

# Transitions the control plane is allowed to make.
ALLOWED_TRANSITIONS = {
    Phase.PENDING: {Phase.SCHEDULED, Phase.FAILED, Phase.TERMINATING},
    Phase.SCHEDULED: {Phase.RUNNING, Phase.FAILED, Phase.TERMINATING},
    Phase.RUNNING: {Phase.SUCCEEDED, Phase.FAILED, Phase.TERMINATING},
    Phase.TERMINATING: {Phase.SUCCEEDED, Phase.FAILED},
    Phase.SUCCEEDED: set(),
    Phase.FAILED: set(),
}


def can_transition(current, target):
    return target in ALLOWED_TRANSITIONS.get(current, set())
