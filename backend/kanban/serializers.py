from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import Board, Comment, Task

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        fullname = validated_data["fullname"].strip()
        parts = fullname.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=first_name,
            last_name=last_name,
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


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
        )


class TaskListSerializer(TaskDetailSerializer):
    comments_count = serializers.SerializerMethodField()

    class Meta(TaskDetailSerializer.Meta):
        fields = TaskDetailSerializer.Meta.fields + ("comments_count",)

    def get_comments_count(self, obj):
        if hasattr(obj, "comments_count"):
            return obj.comments_count
        return obj.comments.count()


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


class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "content", "author", "created_at")
        read_only_fields = ("id", "author", "created_at")

    def get_author(self, obj):
        return _get_fullname(obj.author)


class BoardListSerializer(serializers.ModelSerializer):
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
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status=Task.Status.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(
            priority__in=[Task.Priority.HIGH, Task.Priority.CRITICAL]
        ).count()


class BoardDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="name")
    owner_id = serializers.IntegerField(read_only=True)
    members = BoardMemberSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = (
            "id",
            "title",
            "description",
            "owner_id",
            "members",
            "tasks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_tasks(self, obj):
        tasks = obj.tasks.select_related("assignee", "reviewer").all()
        return TaskDetailSerializer(
            tasks, many=True, context=self.context
        ).data


class BoardWriteSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="name", max_length=255)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Board
        fields = ("id", "title", "description", "members")

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data)
        if members:
            board.members.set(members)
        return board

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance
