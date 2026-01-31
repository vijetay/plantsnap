from django.apps import AppConfig


class PlntConfig(AppConfig):
    name = 'plnt'

    def ready(self):
        from .scheduler import start
        start()
