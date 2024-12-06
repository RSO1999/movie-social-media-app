
# Register your models here.
from django.contrib import admin
from django.apps import apps

# Get all models from your app
app = apps.get_app_config('crossover')  # Replace with your app name
for model in app.get_models():
    admin.site.register(model)
