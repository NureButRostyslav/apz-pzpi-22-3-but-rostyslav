import os
import subprocess
from datetime import datetime

def backup_database(backup_dir='/app/backups', db_name='coworking_db', db_user='coworking_user', db_password='coworking_pass', db_host='db'):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{backup_dir}/db_backup_{timestamp}.sql'
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    subprocess.run([
        'pg_dump',
        '-h', db_host,
        '-U', db_user,
        '-d', db_name,
        '-f', filename
    ], env=env, check=True)
    subprocess.run([
        'find', backup_dir,
        '-name', 'db_backup_*.sql',
        '-mtime', '+7',
        '-delete'
    ], check=True)
    return filename

def restore_database(filename, db_name='coworking_db', db_user='coworking_user', db_password='coworking_pass', db_host='db'):
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    subprocess.run([
        'psql',
        '-h', db_host,
        '-U', db_user,
        '-d', db_name,
        '-f', filename
    ], env=env, check=True)
    return True
