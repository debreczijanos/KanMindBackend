from rest_framework.permissions import BasePermission


class IsTaskBoardMemberOrOwner(BasePermission):
    """Allow access to tasks if the user is part of the related board."""

    def has_object_permission(self, request, view, obj):
        """Check membership/ownership on the task's board."""
        board = getattr(obj, "board", None)
        if board is None:
            return False
        user = request.user
        return board.owner_id == user.id or board.members.filter(id=user.id).exists()
