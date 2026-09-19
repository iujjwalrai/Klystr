# Klystr

A miniature Kubernetes-style container orchestrator. A Django/DRF control plane
stores desired state, a scheduler assigns work to nodes, controllers reconcile
observed state toward desired state, and per-node agents drive a container
runtime.

## Layout

```
config/            Django project: settings, URLs, WSGI/ASGI
apps/
  cluster/         Cluster-scoped objects: namespaces, quotas, events
  nodes/           Node registration, capacity, heartbeats, cordon/drain
  workloads/       Deployments, pods/tasks, specs and lifecycle phases
  scheduler/       Placement: filters, scoring, node assignment
  controllers/     Reconciliation loops that drive actual toward desired state
  agents/          Node-agent API: heartbeats, status reports, work pull
common/            Cross-app helpers: logging, errors, pagination, permissions
infrastructure/
  database/        Advisory locks and other DB-level primitives
  docker/          Container runtime interface, Dockerfile, compose file
  messaging/       Event bus for change notifications
workers/           Long-running control loops (workers/runner.py)
cli/               klystrctl: commands and HTTP client
tests/             Cross-cutting unit and integration tests
```

Each app follows the same shape: `models.py`, `serializers.py`, `views.py`,
`urls.py`, `services.py` (business logic), `admin.py`, `tests/`.

## Getting started

```bash
python -m venv venv
./venv/bin/pip install -r requirements-dev.txt
cp .env.example .env

make services      # Postgres + Redis in Docker
make migrate
make run           # http://127.0.0.1:8000/healthz
```

To run without Docker, set `DB_ENGINE=sqlite` in `.env`.

## Common tasks

| Command | Does |
| --- | --- |
| `make test` | Run the pytest suite |
| `make lint` | Ruff lint |
| `make fmt` | Ruff format |
| `./venv/bin/python manage.py run_worker <name>` | Run one control loop |
| `python -m cli.main` | klystrctl |

## API

Versioned under `/api/v1/`, one prefix per app (`nodes/`, `workloads/`, …).
`/healthz` is an unauthenticated liveness probe.
