from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Board, Comment, Task
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardMemberSerializer,
    BoardWriteSerializer,
    LoginSerializer,
    RegistrationSerializer,
    TaskCommentSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskWriteSerializer,
)

User = get_user_model()


def _user_payload(user):
    full_name = user.get_full_name().strip() or user.username
    return {
        "user_id": user.id,
        "email": user.email,
        "fullname": full_name,
    }


def _auth_response(user, status_code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    payload = _user_payload(user)
    payload["token"] = token.key
    return Response(payload, status=status_code)


def _ensure_board_access(user, board, message=None):
    if board.owner_id == user.id or board.members.filter(id=user.id).exists():
        return
    raise PermissionDenied(message or {"errors": ["You do not have access to this board."]})


class RegisterView(generics.CreateAPIView):
    """
    Registration endpoint consumed by the frontend.
    Expects fullname, email, password, repeated_password.
    """

    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    Token-based login endpoint that mirrors the frontend expectations.
    """

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return _auth_response(user)


class EmailCheckView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"email": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BoardMemberSerializer(user)
        return Response(serializer.data)


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Board.objects.all()

    def get_queryset(self):
        user = self.request.user
        return (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .prefetch_related("members")
            .prefetch_related(
                Prefetch(
                    "tasks",
                    queryset=Task.objects.select_related("assignee", "reviewer"),
                )
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BoardWriteSerializer
        return BoardDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=request.user)
        board.members.add(request.user)
        output_serializer = BoardDetailSerializer(
            board, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_update(self, serializer):
        board = serializer.instance
        if board.owner_id != self.request.user.id:
            raise PermissionDenied(
                {"errors": ["Only the board owner can update this board."]}
            )
        updated_board = serializer.save()
        updated_board.members.add(updated_board.owner)
        return updated_board

    def destroy(self, request, *args, **kwargs):
        board = self.get_object()
        if board.owner_id != request.user.id:
            raise PermissionDenied(
                {"errors": ["Only the board owner can delete this board."]}
            )
        return super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        board = self.get_object()
        serializer = BoardDetailSerializer(
            board, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = BoardListSerializer(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        Task.objects.select_related("board", "assignee", "reviewer")
        .prefetch_related("comments")
        .all()
    )

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(
            Q(board__owner=user) | Q(board__members=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TaskWriteSerializer
        return TaskDetailSerializer

    def _validate_membership(self, board, data=None):
        _ensure_board_access(self.request.user, board)
        if not data:
            return
        for key in ("assignee", "reviewer"):
            user = data.get(key)
            if user and user.id != board.owner_id and not board.members.filter(
                id=user.id
            ).exists():
                raise ValidationError(
                    {f"{key}_id": ["Selected user must be a board member."]}
                )

    def perform_create(self, serializer):
        board = serializer.validated_data["board"]
        self._validate_membership(board, serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        board = serializer.instance.board
        new_board = serializer.validated_data.get("board")
        if new_board and new_board != board:
            raise ValidationError({"board": ["Tasks cannot be moved to another board."]})
        serializer.validated_data.pop("board", None)
        self._validate_membership(board, serializer.validated_data)
        serializer.save(board=board)

    def perform_destroy(self, instance):
        self._validate_membership(instance.board)
        instance.delete()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = TaskDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(detail.data)
        return Response(detail.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail = TaskDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(detail.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class TaskAssignedToMeView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Task.objects.filter(assignee=self.request.user)
            .select_related("board", "assignee", "reviewer")
            .prefetch_related("comments")
        )


class TaskReviewingView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Task.objects.filter(reviewer=self.request.user)
            .select_related("board", "assignee", "reviewer")
            .prefetch_related("comments")
        )


class TaskCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_task(self):
        if not hasattr(self, "_task"):
            task = get_object_or_404(
                Task.objects.select_related("board").prefetch_related("board__members"),
                pk=self.kwargs["task_id"],
            )
            _ensure_board_access(self.request.user, task.board)
            self._task = task
        return self._task

    def get_queryset(self):
        return (
            self.get_task()
            .comments.select_related("author")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        task = self.get_task()
        serializer.save(task=task, author=self.request.user)


class TaskCommentDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskCommentSerializer

    def get_object(self):
        comment = get_object_or_404(
            Comment.objects.select_related("task__board", "author"),
            pk=self.kwargs["comment_id"],
            task_id=self.kwargs["task_id"],
        )
        _ensure_board_access(self.request.user, comment.task.board)
        if (
            comment.author_id != self.request.user.id
            and comment.task.board.owner_id != self.request.user.id
        ):
            raise PermissionDenied(
                {"errors": ["You can only delete your own comments."]}
            )
        return comment
