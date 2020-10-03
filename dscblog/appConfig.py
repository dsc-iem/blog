from django.apps import AppConfig

class AppConfig(AppConfig):
    name = 'dscblog'

    def ready(self):
        import dscblog.signals