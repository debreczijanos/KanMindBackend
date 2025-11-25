from django.urls import path

from .views import BoardViewSet

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
    path("", board_list, name="board-list"),
    path("<int:pk>/", board_detail, name="board-detail"),
    path("<int:pk>", board_detail, name="board-detail-noslash"),
]
