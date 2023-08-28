from django.apps import AppConfig


class NmscdclServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nmscdcl_services'

    def ready(self):
        from . import signals