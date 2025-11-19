from django.contrib import admin

from .models import Board, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "description", "owner__username")
    filter_horizontal = ("members",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "board", "priority", "status", "due_date")
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "board__name")
    filter_horizontal = ("assignees",)
