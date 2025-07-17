from django.urls import path
from .views import (
    StartConversationView,
    SendMessageView,
    ConversationListView,
    ConversationDetailView,
    ChatbotStatsView,
    SessionFeedbackView,
    SystemStatusView
)

app_name = 'skinscan_chatbot'

urlpatterns = [
    # Conversation management
    path('start-chat/', StartConversationView.as_view(), name='start-conversation'),
    path('send-message/', SendMessageView.as_view(), name='send-message'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversation/<uuid:conversation_id>/', ConversationDetailView.as_view(), name='conversation-detail'),

    # Statistics and feedback
    path('stats/', ChatbotStatsView.as_view(), name='chatbot-stats'),
    path('feedback/', SessionFeedbackView.as_view(), name='session-feedback'),

    # System status (public)
    path('status/', SystemStatusView.as_view(), name='system-status'),
]