"""Logging configuration shared by the API, workers and CLI."""

import json
import logging


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per record so logs stay greppable in containers."""

    def format(self, record):
        payload = {
            'ts': self.formatTime(record, '%Y-%m-%dT%H:%M:%S%z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        for key in ('node', 'workload', 'pod', 'controller', 'request_id'):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload)


def build_logging_config(level='INFO', json_output=False):
    formatter = 'json' if json_output else 'console'
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': '{asctime} {levelname:<8} {name} {message}',
                'style': '{',
            },
            'json': {
                '()': 'common.logging.JSONFormatter',
            },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': formatter,
            },
        },
        'root': {
            'handlers': ['stdout'],
            'level': level,
        },
        'loggers': {
            'django': {'handlers': ['stdout'], 'level': level, 'propagate': False},
            'django.db.backends': {'level': 'WARNING', 'propagate': True},
            'klystr': {'handlers': ['stdout'], 'level': level, 'propagate': False},
        },
    }


def get_logger(name):
    """Namespaced logger, e.g. get_logger('scheduler') -> 'klystr.scheduler'."""
    return logging.getLogger(f'klystr.{name}')
