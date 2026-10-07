"""HTTP API for nodes: registration, updates, cordon/uncordon and heartbeats."""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from common.exceptions import InvalidSpec
from common.permissions import IsClusterAdmin

from . import services
from .models import Node
from .serializers import NodeSerializer, NodeUpdateSerializer
from .state import NodeStatus


class NodeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/v1/nodes/                      GET list (?status=Ready), POST register
    /api/v1/nodes/{name}/               GET, PATCH, DELETE
    /api/v1/nodes/{name}/cordon/        POST
    /api/v1/nodes/{name}/uncordon/      POST
    /api/v1/nodes/{name}/heartbeat/     POST
    """

    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    lookup_field = 'name'

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsClusterAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        node_status = self.request.query_params.get('status')
        if node_status:
            if node_status not in NodeStatus.values:
                raise InvalidSpec(f'Unknown node status {node_status!r}.', allowed=NodeStatus.values)
            queryset = queryset.filter(status=node_status)
        return queryset

    def _render(self, node, status_code=status.HTTP_200_OK):
        return Response(NodeSerializer(node).data, status=status_code)

    def create(self, request):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = services.register_node(**serializer.validated_data)
        return self._render(node, status.HTTP_201_CREATED)

    def partial_update(self, request, name=None):
        node = self.get_object()
        serializer = NodeUpdateSerializer(node, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        node = services.update_node(node, **serializer.validated_data)
        return self._render(node)

    @action(detail=True, methods=['post'])
    def cordon(self, request, name=None):
        return self._render(services.cordon(self.get_object()))

    @action(detail=True, methods=['post'])
    def uncordon(self, request, name=None):
        return self._render(services.uncordon(self.get_object()))

    @action(detail=True, methods=['post'])
    def heartbeat(self, request, name=None):
        # Operator-only until node agents get their own credentials (IsNodeAgent).
        return self._render(services.record_heartbeat(self.get_object()))
