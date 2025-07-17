from django.db import models
from django.conf import settings
import uuid


class Conversation(models.Model):
    """Chatbot conversation model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')

    # Conversation metadata
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    # Health context (optional)
    related_analysis = models.ForeignKey(
        'skin_analysis.SkinAnalysis',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Analysis that initiated this conversation"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_message_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        return f"Conversation {self.title or self.id} - {self.user.email}"

    @property
    def message_count(self):
        """Return total number of messages in conversation"""
        return self.messages.count()

    @property
    def last_message(self):
        """Return the last message in conversation"""
        return self.messages.order_by('-created_at').first()

    @property
    def conversation_summary(self):
        """Return conversation summary for display"""
        if self.title:
            return self.title
        elif self.last_message:
            return self.last_message.content[:50] + "..." if len(
                self.last_message.content) > 50 else self.last_message.content
        return f"Conversation started {self.created_at.strftime('%B %d, %Y')}"


class Message(models.Model):
    """Individual message in a conversation"""

    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')

    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()

    # AI response metadata
    response_time = models.FloatField(null=True, blank=True, help_text="AI response time in seconds")
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence in response")

    # Context information
    user_context = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional context like user's recent analyses"
    )

    # Message status
    is_flagged = models.BooleanField(default=False, help_text="Flagged for review")
    flagged_reason = models.CharField(max_length=200, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"{self.message_type.title()} message in {self.conversation.id}"

    @property
    def content_preview(self):
        """Return shortened content for display"""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

    @property
    def is_user_message(self):
        """Check if message is from user"""
        return self.message_type == 'user'

    @property
    def is_assistant_message(self):
        """Check if message is from assistant"""
        return self.message_type == 'assistant'


class ChatbotSession(models.Model):
    """Track chatbot sessions for analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbot_sessions')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='sessions')

    # Session metadata
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    total_messages = models.IntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True)

    # User satisfaction (optional feedback)
    satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],  # 1-5 rating
        help_text="User satisfaction rating (1-5)"
    )
    feedback_comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-session_start']
        verbose_name = 'Chatbot Session'
        verbose_name_plural = 'Chatbot Sessions'

    def __str__(self):
        return f"Session {self.id} - {self.user.email}"

    @property
    def session_duration(self):
        """Calculate session duration if ended"""
        if self.session_end:
            return (self.session_end - self.session_start).total_seconds()
        return None