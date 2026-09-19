"""
Control-loop runner.

Each worker is a loop that reconciles desired state against observed state
on a fixed interval. Run one with:

    python manage.py run_worker <name>
"""

import signal
import time

from common.logging import get_logger

logger = get_logger('worker')


class Worker:
    """Base class for a reconciliation loop."""

    name = 'worker'
    interval_seconds = 5

    def __init__(self, interval_seconds=None):
        if interval_seconds is not None:
            self.interval_seconds = interval_seconds
        self._stopping = False

    def reconcile(self):
        """One pass of the control loop. Subclasses implement this."""
        raise NotImplementedError

    def stop(self, *_args):
        logger.info('stop requested', extra={'controller': self.name})
        self._stopping = True

    def run(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        logger.info('worker started', extra={'controller': self.name})

        while not self._stopping:
            started = time.monotonic()
            try:
                self.reconcile()
            except Exception:
                # A failed pass must not kill the loop; the next one retries.
                logger.exception('reconcile failed', extra={'controller': self.name})

            elapsed = time.monotonic() - started
            time.sleep(max(0.0, self.interval_seconds - elapsed))

        logger.info('worker stopped', extra={'controller': self.name})
