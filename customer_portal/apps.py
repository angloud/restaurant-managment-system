from django.apps import AppConfig


class CustomerPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer_portal'

    def ready(self):
        import customer_portal.signals
