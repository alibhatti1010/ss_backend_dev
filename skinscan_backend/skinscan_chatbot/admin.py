from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message, ChatbotSession


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'conversation_summary', 'message_count',
        'is_active', 'created_at', 'last_message_at'
    ]
    list_filter = [
        'is_active', 'created_at', 'last_message_at'
    ]
    search_fields = [
        'user__email', 'user__username', 'title'
    ]
    raw_id_fields = ['user', 'related_analysis']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_message_at']

    fieldsets = (
        ('Conversation Info', {
            'fields': ('id', 'user', 'title', 'is_active')
        }),
        ('Context', {
            'fields': ('related_analysis',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'No User'

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def message_count(self, obj):
        count = obj.message_count
        if count > 10:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        elif count > 5:
            return format_html(
                '<span style="color: orange;">{}</span>',
                count
            )
        return count

    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'conversation_id', 'message_type', 'content_preview',
        'response_time', 'confidence_score', 'created_at'
    ]
    list_filter = [
        'message_type', 'is_flagged', 'created_at'
    ]
    search_fields = [
        'content', 'conversation__user__email'
    ]
    raw_id_fields = ['conversation']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Message Info', {
            'fields': ('id', 'conversation', 'message_type', 'content')
        }),
        ('AI Metadata', {
            'fields': ('response_time', 'confidence_score', 'user_context')
        }),
        ('Moderation', {
            'fields': ('is_flagged', 'flagged_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def conversation_id(self, obj):
        return str(obj.conversation.id)[:8] + '...'

    conversation_id.short_description = 'Conversation'

    def content_preview(self, obj):
        return obj.content_preview

    content_preview.short_description = 'Content Preview'


@admin.register(ChatbotSession)
class ChatbotSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'session_start', 'session_duration_display',
        'total_messages', 'satisfaction_rating'
    ]
    list_filter = [
        'satisfaction_rating', 'session_start'
    ]
    search_fields = [
        'user__email', 'conversation__title'
    ]
    raw_id_fields = ['user', 'conversation']
    readonly_fields = ['id', 'session_start', 'session_duration']

    fieldsets = (
        ('Session Info', {
            'fields': ('id', 'user', 'conversation')
        }),
        ('Session Data', {
            'fields': ('session_start', 'session_end', 'session_duration',
                       'total_messages', 'average_response_time')
        }),
        ('Feedback', {
            'fields': ('satisfaction_rating', 'feedback_comment')
        }),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def session_duration_display(self, obj):
        duration = obj.session_duration
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s"
        return 'Ongoing'

    session_duration_display.short_description = 'Duration'