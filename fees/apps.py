from django.apps import AppConfig


class FeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fees'

    def ready(self):
        # import signals
        try:
            import fees.signals  # noqa: F401
        except Exception:
            pass
