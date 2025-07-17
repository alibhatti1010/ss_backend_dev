from rest_framework import serializers
from django.utils import timezone
from .models import Conversation, Message, ChatbotSession


class MessageSerializer(serializers.ModelSerializer):
    content_preview = serializers.ReadOnlyField()
    is_user_message = serializers.ReadOnlyField()
    is_assistant_message = serializers.ReadOnlyField()

    class Meta:
        model = Message
        fields = [
            'id', 'message_type', 'content', 'content_preview',
            'response_time', 'confidence_score', 'is_user_message',
            'is_assistant_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'response_time', 'confidence_score', 'created_at', 'updated_at']


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    conversation_summary = serializers.ReadOnlyField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'is_active', 'message_count', 'last_message',
            'conversation_summary', 'created_at', 'updated_at',
            'last_message_at', 'messages'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message_at']

    def get_last_message(self, obj):
        if obj.last_message:
            return {
                'content': obj.last_message.content_preview,
                'message_type': obj.last_message.message_type,
                'created_at': obj.last_message.created_at
            }
        return None


class ConversationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for conversation list view"""
    message_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    conversation_summary = serializers.ReadOnlyField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'conversation_summary', 'is_active',
            'message_count', 'last_message', 'created_at', 'last_message_at'
        ]

    def get_last_message(self, obj):
        if obj.last_message:
            return {
                'content': obj.last_message.content_preview,
                'message_type': obj.last_message.message_type,
                'created_at': obj.last_message.created_at
            }
        return None


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)
    conversation_id = serializers.UUIDField(required=False)
    analysis_id = serializers.UUIDField(required=False)

    def validate_content(self, value):
        """Validate message content"""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")

        if len(value.strip()) < 3:
            raise serializers.ValidationError("Message must be at least 3 characters long.")

        return value.strip()

    def validate(self, attrs):
        """Cross-field validation"""
        content = attrs.get('content', '').lower()

        # Basic content filtering
        inappropriate_words = ['spam', 'test123', 'hello world']
        if any(word in content for word in inappropriate_words):
            # Don't block, just flag for review
            attrs['_flag_for_review'] = True

        return attrs


class StartConversationSerializer(serializers.Serializer):
    initial_message = serializers.CharField(max_length=2000)
    title = serializers.CharField(max_length=200, required=False)
    analysis_id = serializers.UUIDField(required=False)

    def validate_initial_message(self, value):
        """Validate initial message"""
        if not value.strip():
            raise serializers.ValidationError("Initial message cannot be empty.")

        if len(value.strip()) < 3:
            raise serializers.ValidationError("Initial message must be at least 3 characters long.")

        return value.strip()


class ConversationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['title', 'is_active']

    def validate_title(self, value):
        """Validate conversation title"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value.strip() if value else value


class ChatbotSessionSerializer(serializers.ModelSerializer):
    session_duration = serializers.ReadOnlyField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = ChatbotSession
        fields = [
            'id', 'user_email', 'session_start', 'session_end',
            'session_duration', 'total_messages', 'average_response_time',
            'satisfaction_rating', 'feedback_comment'
        ]
        read_only_fields = ['id', 'session_start', 'session_duration']

    def get_user_email(self, obj):
        return obj.user.email


class SessionFeedbackSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    satisfaction_rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback_comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate_feedback_comment(self, value):
        """Validate feedback comment"""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError("Feedback comment cannot exceed 1000 characters.")
        return value.strip() if value else value


class ConversationStatsSerializer(serializers.Serializer):
    """Serializer for conversation statistics"""
    total_conversations = serializers.IntegerField()
    active_conversations = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    average_messages_per_conversation = serializers.FloatField()
    most_recent_conversation = serializers.DateTimeField()


class UserChatHistorySerializer(serializers.Serializer):
    """Serializer for user's complete chat history with summary"""
    total_conversations = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    conversations = ConversationListSerializer(many=True)
    recent_activity = serializers.ListField()
    common_topics = serializers.ListField()