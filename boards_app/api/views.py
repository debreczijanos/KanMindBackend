from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from boards_app.models import Board
from tasks_app.models import Task
from .permissions import IsBoardMemberOrOwner
from .serializers import BoardDetailSerializer, BoardListSerializer, BoardWriteSerializer


class BoardViewSet(viewsets.ModelViewSet):
    """Board CRUD plus authenticated listings for owners and members."""

    permission_classes = [permissions.IsAuthenticated, IsBoardMemberOrOwner]
    base_queryset = (
        Board.objects.select_related("owner")
        .prefetch_related("members")
        .prefetch_related(
            Prefetch(
                "tasks",
                queryset=Task.objects.select_related("assignee", "reviewer").prefetch_related("comments"),
            )
        )
    )
    queryset = base_queryset

    def get_queryset(self):
        """Restrict boards to those the user owns or is a member of."""
        user = self.request.user
        return self.base_queryset.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        """Switch serializer based on action to control payload size."""
        if self.action == "list":
            return BoardListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BoardWriteSerializer
        return BoardDetailSerializer

    def get_object(self):
        """Fetch a single board and enforce object-level permissions."""
        board = get_object_or_404(self.base_queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, board)
        return board

    def create(self, request, *args, **kwargs):
        """Create a board with the requester as owner and member."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=request.user)
        board.members.add(request.user)
        output_serializer = BoardDetailSerializer(board, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        """Allow updates only from the owner and keep owner in members."""
        board = serializer.instance
        if board.owner_id != self.request.user.id:
            raise PermissionDenied({"errors": ["Only the board owner can update this board."]})
        updated_board = serializer.save()
        updated_board.members.add(updated_board.owner)
        return updated_board

    def destroy(self, request, *args, **kwargs):
        """Restrict delete operations to the board owner."""
        board = self.get_object()
        if board.owner_id != request.user.id:
            raise PermissionDenied({"errors": ["Only the board owner can delete this board."]})
        return super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Return a board with nested tasks and members."""
        board = self.get_object()
        serializer = BoardDetailSerializer(board, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update a board and return the detailed payload."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_board = self.perform_update(serializer)
        output = BoardDetailSerializer(updated_board, context=self.get_serializer_context())
        return Response(output.data)

    def partial_update(self, request, *args, **kwargs):
        """Support PATCH by delegating to the main update flow."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
