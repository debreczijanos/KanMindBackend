from django.urls import path

from .views import (
    BoardViewSet,
    EmailCheckView,
    LoginView,
    RegisterView,
    TaskAssignedToMeView,
    TaskCommentDetailView,
    TaskCommentListCreateView,
    TaskReviewingView,
    TaskViewSet,
)

board_list = BoardViewSet.as_view({
    "get": "list",
    "post": "create",
})
board_detail = BoardViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "put": "update",
    "delete": "destroy",
})

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
    path("registration/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("boards/", board_list, name="board-list"),
    path("boards/<int:pk>/", board_detail, name="board-detail"),
    path("boards/<int:pk>", board_detail, name="board-detail-noslash"),
    path("tasks/", task_list, name="task-list"),
    path("tasks/<int:pk>/", task_detail, name="task-detail"),
    path("tasks/<int:pk>", task_detail, name="task-detail-noslash"),
    path("tasks/assigned-to-me/", TaskAssignedToMeView.as_view(), name="tasks-assigned"),
    path("tasks/reviewing/", TaskReviewingView.as_view(), name="tasks-reviewing"),
    path(
        "tasks/<int:task_id>/comments/",
        TaskCommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        TaskCommentDetailView.as_view(),
        name="task-comment-detail",
    ),
]
