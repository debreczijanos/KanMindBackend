from django.contrib.auth import get_user_model
from rest_framework import serializers

from auth_app.api.serializers import UserLookupSerializer
from tasks_app.api.serializers import TaskDetailSerializer
from boards_app.models import Board
from tasks_app.models import Task

User = get_user_model()


class BoardListSerializer(serializers.ModelSerializer):
    """Lightweight board listing payload with counters."""
    title = serializers.CharField(source="name")
    owner_id = serializers.IntegerField(read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = (
            "id",
            "title",
            "owner_id",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
        )

    def get_member_count(self, obj):
        """Total members on the board."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Total tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Tasks still in 'to-do' status."""
        return obj.tasks.filter(status=Task.Status.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        """Tasks flagged as high or critical priority."""
        return obj.tasks.filter(priority__in=[Task.Priority.HIGH, Task.Priority.CRITICAL]).count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Full board detail including members and nested tasks."""
    title = serializers.CharField(source="name")
    owner_id = serializers.IntegerField(read_only=True)
    owner_data = UserLookupSerializer(source="owner", read_only=True)
    members = UserLookupSerializer(many=True, read_only=True)
    members_data = UserLookupSerializer(source="members", many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = (
            "id",
            "title",
            "description",
            "owner_id",
            "owner_data",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "members",
            "members_data",
            "tasks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_tasks(self, obj):
        """Return nested tasks with assignee/reviewer details."""
        tasks = obj.tasks.select_related("assignee", "reviewer").all()
        return TaskDetailSerializer(tasks, many=True, context=self.context).data

    def get_member_count(self, obj):
        """Total members on the board."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Total tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Tasks still in 'to-do' status."""
        return obj.tasks.filter(status=Task.Status.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        """Tasks flagged as high or critical priority."""
        return obj.tasks.filter(priority__in=[Task.Priority.HIGH, Task.Priority.CRITICAL]).count()


class BoardWriteSerializer(serializers.ModelSerializer):
    """Input serializer for board create/update operations."""
    title = serializers.CharField(source="name", max_length=255)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Board
        fields = ("id", "title", "description", "members")

    def create(self, validated_data):
        """Create a board and optionally attach members."""
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data)
        if members:
            board.members.set(members)
        return board

    def update(self, instance, validated_data):
        """Update board fields and replace members when provided."""
        members = validated_data.pop("members", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance


class BoardMembershipSerializer(serializers.ModelSerializer):
    """Minimal payload focused on owner and members after updates."""

    title = serializers.CharField(source="name")
    owner_data = UserLookupSerializer(source="owner", read_only=True)
    members_data = UserLookupSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ("id", "title", "owner_data", "members_data")
