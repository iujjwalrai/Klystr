"""
Postgres advisory locks.

Controllers use these so only one replica reconciles a given resource at a
time, without adding a separate coordination service.
"""

import contextlib
import hashlib

from django.db import connection


def _lock_key(name):
    digest = hashlib.blake2b(name.encode(), digest_size=8).digest()
    # Postgres advisory locks take a signed 64-bit integer.
    return int.from_bytes(digest, 'big', signed=True)


@contextlib.contextmanager
def advisory_lock(name, blocking=True):
    """
    Hold a session-level advisory lock for `name`.

    Yields True when the lock was acquired. With blocking=False it yields
    False immediately if another session holds it.
    """
    if connection.vendor != 'postgresql':
        # SQLite dev setups run a single process, so there is nothing to coordinate.
        yield True
        return

    key = _lock_key(name)
    with connection.cursor() as cursor:
        if blocking:
            cursor.execute('SELECT pg_advisory_lock(%s)', [key])
            acquired = True
        else:
            cursor.execute('SELECT pg_try_advisory_lock(%s)', [key])
            acquired = cursor.fetchone()[0]

        try:
            yield acquired
        finally:
            if acquired:
                cursor.execute('SELECT pg_advisory_unlock(%s)', [key])
