"""Small helpers shared across apps."""

import re
import secrets
from datetime import timedelta

from django.utils import timezone

# Same shape as a Kubernetes RFC 1123 label: lowercase alphanumeric and dashes.
NAME_RE = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
MAX_NAME_LENGTH = 63


def is_valid_name(name):
    return bool(name) and len(name) <= MAX_NAME_LENGTH and bool(NAME_RE.match(name))


def generate_suffix(length=5):
    """Random suffix used when the control plane names a child object."""
    alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def derive_name(prefix, suffix_length=5):
    """e.g. derive_name('web') -> 'web-k29fq', truncated to fit the limit."""
    suffix = generate_suffix(suffix_length)
    head = prefix[: MAX_NAME_LENGTH - len(suffix) - 1]
    return f'{head}-{suffix}'


def utcnow():
    return timezone.now()


def is_stale(timestamp, timeout_seconds):
    """True when `timestamp` is missing or older than the timeout."""
    if timestamp is None:
        return True
    return timezone.now() - timestamp > timedelta(seconds=timeout_seconds)


def parse_cpu(value):
    """Parse a CPU quantity ('500m', '2', 1.5) into float cores."""
    if isinstance(value, int | float):
        return float(value)
    value = str(value).strip()
    if value.endswith('m'):
        return float(value[:-1]) / 1000.0
    return float(value)


MEMORY_UNITS = {
    'Ki': 1024,
    'Mi': 1024 ** 2,
    'Gi': 1024 ** 3,
    'Ti': 1024 ** 4,
    'K': 1000,
    'M': 1000 ** 2,
    'G': 1000 ** 3,
    'T': 1000 ** 4,
}


def parse_memory(value):
    """Parse a memory quantity ('512Mi', '2Gi', 1024) into bytes."""
    if isinstance(value, int | float):
        return int(value)
    value = str(value).strip()
    for unit, factor in MEMORY_UNITS.items():
        if value.endswith(unit):
            return int(float(value[: -len(unit)]) * factor)
    return int(float(value))
