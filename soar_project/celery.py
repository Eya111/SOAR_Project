# soar_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# définir le module settings par défaut pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soar_project.settings')

app = Celery('soar_project')

# Charger la configuration depuis settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans chaque app
app.autodiscover_tasks()
