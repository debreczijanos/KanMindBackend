from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Board
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardMemberSerializer,
    BoardWriteSerializer,
    LoginSerializer,
    RegistrationSerializer,
)

User = get_user_model()


def _user_payload(user):
    full_name = user.get_full_name().strip() or user.username
    return {
        "user_id": user.id,
        "email": user.email,
        "fullname": full_name,
    }


def _auth_response(user, status_code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    payload = _user_payload(user)
    payload["token"] = token.key
    return Response(payload, status=status_code)


class RegisterView(generics.CreateAPIView):
    """
    Registration endpoint consumed by the frontend.
    Expects fullname, email, password, repeated_password.
    """

    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    Token-based login endpoint that mirrors the frontend expectations.
    """

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return _auth_response(user)


class EmailCheckView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"email": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BoardMemberSerializer(user)
        return Response(serializer.data)


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Board.objects.all()

    def get_queryset(self):
        user = self.request.user
        return (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .prefetch_related("members")
            .prefetch_related("tasks")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BoardWriteSerializer
        return BoardDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=request.user)
        board.members.add(request.user)
        output_serializer = BoardDetailSerializer(
            board, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_update(self, serializer):
        board = serializer.instance
        if board.owner_id != self.request.user.id:
            raise PermissionDenied(
                {"errors": ["Only the board owner can update this board."]}
            )
        updated_board = serializer.save()
        updated_board.members.add(updated_board.owner)
        return updated_board

    def destroy(self, request, *args, **kwargs):
        board = self.get_object()
        if board.owner_id != request.user.id:
            raise PermissionDenied(
                {"errors": ["Only the board owner can delete this board."]}
            )
        return super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        board = self.get_object()
        serializer = BoardDetailSerializer(
            board, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = BoardListSerializer(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
