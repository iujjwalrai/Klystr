"""Domain errors and the DRF exception handler that renders them."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class KlystrError(Exception):
    """Base class for control-plane errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    reason = 'KlystrError'

    def __init__(self, message=None, **details):
        super().__init__(message or self.reason)
        self.message = message or self.reason
        self.details = details


class ResourceConflict(KlystrError):
    """Optimistic-concurrency failure: the object changed under us."""

    status_code = status.HTTP_409_CONFLICT
    reason = 'Conflict'


class SchedulingError(KlystrError):
    """No node can satisfy a workload's requirements."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    reason = 'Unschedulable'


class NodeUnavailable(KlystrError):
    """Target node is not Ready or is cordoned."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    reason = 'NodeUnavailable'


class InvalidSpec(KlystrError):
    """A submitted spec failed validation."""

    status_code = status.HTTP_400_BAD_REQUEST
    reason = 'InvalidSpec'


def api_exception_handler(exc, context):
    """Render KlystrError subclasses as structured JSON; defer to DRF otherwise."""
    if isinstance(exc, KlystrError):
        return Response(
            {'reason': exc.reason, 'message': exc.message, 'details': exc.details},
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is not None and not isinstance(response.data, dict):
        response.data = {'reason': 'Error', 'message': response.data}
    return response
