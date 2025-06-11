import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coworking_system.settings')
app = Celery('coworking_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'daily-backup': {
        'task': 'api.tasks.daily_database_backup',
        'schedule': crontab(hour=0, minute=0),
    },
}