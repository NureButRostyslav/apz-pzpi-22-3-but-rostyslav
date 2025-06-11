from celery import shared_task
import shutil
from django.conf import settings
from datetime import datetime
from django.core.management import call_command

@shared_task
def daily_database_backup():
    call_command('dbbackup')
    
    backup_path = settings.BASE_DIR / 'backups' / f'db_backup_{timestamp}.sqlite3'
    shutil.copy(settings.DATABASES['default']['NAME'], backup_path)