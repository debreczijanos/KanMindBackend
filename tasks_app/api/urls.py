from django.urls import path

from .views import (
    TaskAssignedToMeView,
    TaskCommentDetailView,
    TaskCommentListCreateView,
    TaskReviewingView,
    TaskViewSet,
)

task_list = TaskViewSet.as_view({
    "get": "list",
    "post": "create",
})
task_detail = TaskViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "put": "update",
    "delete": "destroy",
})

urlpatterns = [
    path("", task_list, name="task-list"),
    path("<int:pk>/", task_detail, name="task-detail"),
    path("<int:pk>", task_detail, name="task-detail-noslash"),
    path("assigned-to-me/", TaskAssignedToMeView.as_view(), name="tasks-assigned"),
    path("reviewing/", TaskReviewingView.as_view(), name="tasks-reviewing"),
    path("<int:task_id>/comments/", TaskCommentListCreateView.as_view(), name="task-comments"),
    path("<int:task_id>/comments/<int:comment_id>/", TaskCommentDetailView.as_view(), name="task-comment-detail"),
]
