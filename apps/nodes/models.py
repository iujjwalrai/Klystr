from django.db import models
from django.core.exceptions import ValidationError
# Create your models here.

class NodeStatus(models.TextChoices):
    READY = 'Ready', 'Ready',
    NOT_READY = 'NotReady', 'NotReady',
    CORDONED = 'Cordoned', 'Cordoned',
    DRAINING = 'Draining', 'Draining',


SCHEDULABLE_STATUSES = {
    NodeStatus.READY,
}

def is_valid_name(value):
    if not value:
        raise ValidationError("Name cannot be empty.")
    

    if(len(value) > 63):
        raise ValidationError("Name cannot be longer than 63 characters.")
    

    allowed_set = set("abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789-")
    if any(char not in allowed_set for char in value):
        raise ValidationError("Node Name can only contain alphanumeric characters and hyphens.")
    
    if value.startswith('-') or value.endswith('-'):
        raise ValidationError("Node Name cannot start or end with a hyphen.")
    



class Node(models.Model):
    name = models.CharField(
        max_length=63,
        unique=True,
        validators=[is_valid_name],
    )

    status=models.CharField(
        max_length=10,
        choices=NodeStatus.choices,
        default=NodeStatus.NOT_READY,
    )

    cpu_capacity=models.PositiveIntegerField(
        help_text="CPU capacity in millicores (m). For example, 1000m = 1 CPU core."
    )

    memory_capacity=models.PositiveBigIntegerField(
        help_text="Memory capacity in bytes. For example, 1073741824 bytes = 1 GiB."
    )

    allocable=models.JSONField(
        default=dict,
        blank=True,
    )

    labels=models.JSONField(
        default=dict,
        blank=True,
    )

    unschedulable=models.BooleanField(
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
        ordering=["name"]
    

    def __str__(self):
        return self.name
    

    @property
    def is_schedulable(self):
        return (
            self.status in SCHEDULABLE_STATUSES
            and not self.unschedulable
        )
    
    


