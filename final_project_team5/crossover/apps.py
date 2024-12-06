from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate

class CrossoverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crossover'

    # Will call the populate_movies script after the database is migrated
    def ready(self):
        post_migrate.connect(self.populate_movies, sender=self)

    def populate_movies(self, **kwargs):
        from .models import Movie
        if not Movie.objects.exists():
            call_command('populate_movies')
