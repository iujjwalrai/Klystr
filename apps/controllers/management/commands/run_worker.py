"""Run a single control loop in the foreground: `manage.py run_worker <name>`."""

from django.core.management.base import BaseCommand, CommandError

# Populated as loops land in workers/tasks/.
WORKERS = {}


class Command(BaseCommand):
    help = 'Run a Klystr control loop.'

    def add_arguments(self, parser):
        known = ', '.join(sorted(WORKERS)) or '(none registered yet)'
        parser.add_argument('name', help=f'One of: {known}')
        parser.add_argument(
            '--interval', type=float, default=None,
            help='Override the loop interval, in seconds',
        )

    def handle(self, *args, **options):
        name = options['name']
        if name not in WORKERS:
            raise CommandError(f'unknown worker {name!r}; registered: {sorted(WORKERS)}')

        worker = WORKERS[name](interval_seconds=options['interval'])
        worker.run()
