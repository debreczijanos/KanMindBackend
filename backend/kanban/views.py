from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer


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
