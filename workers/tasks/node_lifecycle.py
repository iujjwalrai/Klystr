"""Marks nodes NotReady when their agents stop heartbeating."""

from django.conf import settings

from apps.nodes import services
from common.logging import get_logger
from infrastructure.database.locks import advisory_lock
from workers.runner import Worker

logger = get_logger('node-lifecycle')


class NodeLifecycleWorker(Worker):
    name = 'node-lifecycle'
    interval_seconds = settings.KLYSTR['RECONCILE_INTERVAL_SECONDS']

    def reconcile(self):
        # Several replicas may run; only the one holding the lock does the pass.
        with advisory_lock(self.name, blocking=False) as acquired:
            if not acquired:
                return []

            marked = services.mark_stale_nodes()
            for node in marked:
                logger.warning(
                    'node marked NotReady: heartbeat timed out',
                    extra={'controller': self.name, 'node': node.name},
                )
            return marked
