from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    """Allow access to board owners or members."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.owner_id == user.id or obj.members.filter(id=user.id).exists()
