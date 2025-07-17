from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    analysis_count = serializers.ReadOnlyField()
    conversation_count = serializers.ReadOnlyField()
    total_messages_sent = serializers.ReadOnlyField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'date_of_birth',
            'profile_picture', 'is_email_verified', 'analysis_count',
            'conversation_count', 'total_messages_sent',
            'created_at', 'profile'
        ]
        read_only_fields = ['id', 'email', 'is_email_verified', 'created_at']

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'bio': profile.bio,
                'location': profile.location,
                'website': profile.website,
                'skin_type': profile.skin_type,
                'profile_visibility': profile.profile_visibility,
                'email_notifications': profile.email_notifications,
                'analysis_reminders': profile.analysis_reminders
            }
        except UserProfile.DoesNotExist:
            return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    profile_data = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'profile_picture', 'profile_data'
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile_data', {})

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                if hasattr(profile, attr):
                    setattr(profile, attr, value)
            profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password fields didn't match.")
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserAnalysisHistorySerializer(serializers.Serializer):
    """Serializer for user's analysis history with summary"""
    total_analyses = serializers.IntegerField()
    recent_analyses = serializers.ListField()
    most_common_conditions = serializers.ListField()


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Public profile serializer (limited fields)"""
    full_name = serializers.ReadOnlyField()
    analysis_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'analysis_count', 'created_at'
        ]
        read_only_fields = fields