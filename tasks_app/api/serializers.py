from django.contrib.auth import get_user_model
from rest_framework import serializers

from boards_app.models import Board
from tasks_app.models import Comment, Task

User = get_user_model()


def _get_fullname(user: User) -> str:
    full_name = user.get_full_name().strip()
    return full_name or user.username


class BoardMemberSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "fullname")

    def get_fullname(self, obj):
        return _get_fullname(obj)


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = BoardMemberSerializer(read_only=True)
    reviewer = BoardMemberSerializer(read_only=True)
    board = serializers.IntegerField(source="board_id", read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "assignee",
            "reviewer",
            "comments_count",
        )

    def get_comments_count(self, obj):
        if hasattr(obj, "comments_count"):
            return obj.comments_count
        return obj.comments.count()


class TaskListSerializer(TaskDetailSerializer):
    class Meta(TaskDetailSerializer.Meta):
        fields = TaskDetailSerializer.Meta.fields


class TaskWriteSerializer(serializers.ModelSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
        source="assignee",
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
        source="reviewer",
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "assignee_id",
            "reviewer_id",
        )

    def validate_board(self, value):
        if not Board.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Board does not exist.")
        return value


class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "content", "author", "created_at")
        read_only_fields = ("id", "author", "created_at")

    def get_author(self, obj):
        return _get_fullname(obj.author)
