from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    """Allow access to board owners or members."""

    def has_object_permission(self, request, view, obj):
        """Grant permission if the user owns or belongs to the board."""
        user = request.user
        return obj.owner_id == user.id or obj.members.filter(id=user.id).exists()
