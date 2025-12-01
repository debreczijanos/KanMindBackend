from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


def _get_fullname(user: User) -> str:
    """Return a trimmed full name fallback to username."""
    full_name = user.get_full_name().strip()
    return full_name or user.username


class RegistrationSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        """Disallow duplicate registrations by email (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Ensure the repeated password matches."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError({"repeated_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        fullname = validated_data["fullname"].strip()
        parts = fullname.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=first_name,
            last_name=last_name,
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate by email; surface a generic error on failure."""
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class UserLookupSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "fullname")

    def get_fullname(self, obj):
        """Expose the formatted name for lookups."""
        return _get_fullname(obj)
