from django.apps import AppConfig


class SkinscanChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'skinscan_chatbot'
    verbose_name = 'SkinScan Chatbot'

    def ready(self):
        # Import signals if needed in future
        pass