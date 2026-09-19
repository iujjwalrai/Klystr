"""Permission classes separating human operators from node agents."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsClusterAdmin(BasePermission):
    """Full read/write access to cluster-scoped resources."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class IsReadOnly(BasePermission):
    """Allow GET/HEAD/OPTIONS only."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsNodeAgent(BasePermission):
    """
    Grants an authenticated node agent access to its own node's endpoints.

    Views using this must expose `get_node()` returning the node the request
    targets, so an agent cannot report state on behalf of another node.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'agent_node_id', None))

    def has_object_permission(self, request, view, obj):
        node_id = getattr(obj, 'node_id', None) or getattr(obj, 'id', None)
        return node_id == request.user.agent_node_id
