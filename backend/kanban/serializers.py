from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Board, Task

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TaskSerializer(serializers.ModelSerializer):
    assignees = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "priority",
            "status",
            "assignees",
            "due_date",
            "created_at",
            "updated_at",
            "board",
        )
        read_only_fields = ("created_at", "updated_at")


class BoardSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = (
            "id",
            "name",
            "description",
            "owner",
            "members",
            "tasks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
