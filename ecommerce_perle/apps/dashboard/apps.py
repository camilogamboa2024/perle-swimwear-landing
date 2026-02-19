from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Panel'

    def ready(self):
        # Register admin custom URLs once app registry is ready.
        from . import admin_urls  # noqa: F401
