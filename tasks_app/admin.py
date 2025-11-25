from django.contrib import admin

from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "board", "priority", "status", "assignee", "reviewer", "due_date")
    list_filter = ("priority", "status", "board")
    search_fields = ("title", "description", "board__name")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("task__title", "author__email", "content")
