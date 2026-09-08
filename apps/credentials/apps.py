from django.apps import AppConfig


class CredentialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.credentials'
    # Drives the heading of this app's section on the admin index page.
    verbose_name = 'DIDA Credentials'
