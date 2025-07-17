from django.apps import AppConfig


class SkinscanAuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'skinscan_authentication'
    verbose_name = 'SkinScan Authentication'

    def ready(self):
        import skinscan_authentication.signals