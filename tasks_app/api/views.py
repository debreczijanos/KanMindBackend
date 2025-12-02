from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from boards_app.models import Board
from tasks_app.api.permissions import IsTaskBoardMemberOrOwner
from tasks_app.api.serializers import (
    TaskCommentSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskWriteSerializer,
)
from tasks_app.models import Comment, Task


def _ensure_board_access(user, board, message=None):
    """Raise PermissionDenied if the user is neither board owner nor member."""
    if board.owner_id == user.id or board.members.filter(id=user.id).exists():
        return
    raise PermissionDenied(message or {"errors": ["You do not have access to this board."]})


class TaskViewSet(viewsets.ModelViewSet):
    """Task CRUD with membership validation for boards."""

    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMemberOrOwner]
    base_queryset = (
        Task.objects.select_related("board", "assignee", "reviewer")
        .select_related("board__owner")
        .prefetch_related("comments", "board__members")
        .all()
    )
    queryset = base_queryset

    def get_queryset(self):
        """Only expose tasks on boards the user belongs to."""
        user = self.request.user
        return self.queryset.filter(Q(board__owner=user) | Q(board__members=user)).distinct()

    def get_object(self):
        """Fetch a task and enforce board membership before perms."""
        task = get_object_or_404(self.base_queryset, pk=self.kwargs["pk"])
        _ensure_board_access(self.request.user, task.board)
        self.check_object_permissions(self.request, task)
        return task

    def get_serializer_class(self):
        """Use write serializer for mutations, detail for reads."""
        if self.action in ("create", "update", "partial_update"):
            return TaskWriteSerializer
        return TaskDetailSerializer

    def _validate_membership(self, board, data=None):
        """Validate that assignee/reviewer are part of the board."""
        _ensure_board_access(self.request.user, board)
        if not data:
            return
        for key in ("assignee", "reviewer"):
            user = data.get(key)
            if user and user.id != board.owner_id and not board.members.filter(id=user.id).exists():
                raise ValidationError({f"{key}_id": ["Selected user must be a board member."]})

    def perform_create(self, serializer):
        """Validate board membership and persist a new task."""
        board = serializer.validated_data["board"]
        self._validate_membership(board, serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        """Disallow moving tasks between boards and revalidate members."""
        board = serializer.instance.board
        new_board = serializer.validated_data.get("board")
        if new_board and new_board != board:
            raise ValidationError({"board": ["Tasks cannot be moved to another board."]})
        serializer.validated_data.pop("board", None)
        self._validate_membership(board, serializer.validated_data)
        serializer.save(board=board)

    def perform_destroy(self, instance):
        """Ensure the user can access the board before delete."""
        self._validate_membership(instance.board)
        instance.delete()

    def create(self, request, *args, **kwargs):
        """Return a detailed payload after task creation."""
        board_id = request.data.get("board")
        if board_id is not None and not Board.objects.filter(id=board_id).exists():
            raise NotFound({"board": "Board not found."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = TaskDetailSerializer(serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(detail.data)
        return Response(detail.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Update a task and return the detailed view."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail = TaskDetailSerializer(serializer.instance, context=self.get_serializer_context())
        return Response(detail.data)

    def partial_update(self, request, *args, **kwargs):
        """Support PATCH updates through the same flow as PUT."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class TaskAssignedToMeView(generics.ListAPIView):
    """Tasks where the authenticated user is the assignee."""

    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Tasks where the current user is assigned."""
        return Task.objects.filter(assignee=self.request.user).select_related("board", "assignee", "reviewer").prefetch_related("comments")


class TaskReviewingView(generics.ListAPIView):
    """Tasks where the authenticated user is the reviewer."""

    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Tasks where the current user is reviewer."""
        return Task.objects.filter(reviewer=self.request.user).select_related("board", "assignee", "reviewer").prefetch_related("comments")


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """List and create comments on a task within a board context."""

    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_task(self):
        """Cache and return the task with board membership enforced."""
        if not hasattr(self, "_task"):
            task = get_object_or_404(
                Task.objects.select_related("board").prefetch_related("board__members"),
                pk=self.kwargs["task_id"],
            )
            _ensure_board_access(self.request.user, task.board)
            self._task = task
        return self._task

    def get_queryset(self):
        """Comments on the task ordered by creation time."""
        return self.get_task().comments.select_related("author").order_by("created_at")

    def perform_create(self, serializer):
        """Attach the comment to the task and current user."""
        task = self.get_task()
        serializer.save(task=task, author=self.request.user)


class TaskCommentDetailView(generics.DestroyAPIView):
    """Delete a specific comment if author or board owner."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskCommentSerializer

    def get_object(self):
        """Allow deletion by comment author or board owner only."""
        comment = get_object_or_404(
            Comment.objects.select_related("task__board", "author"),
            pk=self.kwargs["comment_id"],
            task_id=self.kwargs["task_id"],
        )
        _ensure_board_access(self.request.user, comment.task.board)
        if comment.author_id != self.request.user.id and comment.task.board.owner_id != self.request.user.id:
            raise PermissionDenied({"errors": ["You can only delete your own comments."]})
        return comment
