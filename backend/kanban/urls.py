from django.urls import path

from .views import BoardViewSet, EmailCheckView, LoginView, RegisterView

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

urlpatterns = [
    path("registration/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("boards/", board_list, name="board-list"),
    path("boards/<int:pk>/", board_detail, name="board-detail"),
    path("boards/<int:pk>", board_detail, name="board-detail-noslash"),
]
