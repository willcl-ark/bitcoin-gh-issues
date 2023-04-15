#!/usr/bin/env python3

import os
import glob
import shutil
import time
from datetime import datetime, timedelta

APP_PATH = '/home/ubuntu/bitcoin-issues'
DB_NAME = os.path.join(APP_PATH, 'issues.db')
BACKUP_DIR = os.path.join(APP_PATH, 'db_backups')


def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_filename = f'{DB_NAME}_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(DB_NAME, backup_path)
    print(f'Database backup created: {backup_path}')


def get_backup_files():
    return glob.glob(os.path.join(BACKUP_DIR, '*.db'))


def backup_files_by_age(backup_files):
    now = datetime.now()
    backups_by_age = {
        'most_recent': (None, None),
        'last_hour': (None, None),
        'last_day': (None, None),
        'last_week': (None, None),
        'last_month': (None, None),
    }

    for backup_file in backup_files:
        timestamp = os.path.getmtime(backup_file)
        backup_datetime = datetime.fromtimestamp(timestamp)
        age = now - backup_datetime

        if backups_by_age['most_recent'][1] is None or backup_datetime > backups_by_age['most_recent'][1]:
            backups_by_age['most_recent'] = (backup_file, backup_datetime)

        if age < timedelta(hours=1) and (backups_by_age['last_hour'][1] is None or backup_datetime > backups_by_age['last_hour'][1]):
            backups_by_age['last_hour'] = (backup_file, backup_datetime)

        if age < timedelta(days=1) and (backups_by_age['last_day'][1] is None or backup_datetime > backups_by_age['last_day'][1]):
            backups_by_age['last_day'] = (backup_file, backup_datetime)

        if age < timedelta(weeks=1) and (backups_by_age['last_week'][1] is None or backup_datetime > backups_by_age['last_week'][1]):
            backups_by_age['last_week'] = (backup_file, backup_datetime)

        if age < timedelta(days=30) and (backups_by_age['last_month'][1] is None or backup_datetime > backups_by_age['last_month'][1]):
            backups_by_age['last_month'] = (backup_file, backup_datetime)

    return backups_by_age


def cleanup_backups():
    backup_files = get_backup_files()
    backups_by_age = backup_files_by_age(backup_files)

    backups_to_keep = {backup[0] for backup in backups_by_age.values() if backup is not None}

    for backup_file in backup_files:
        if backup_file not in backups_to_keep:
            os.remove(backup_file)
            print(f'Removed backup: {backup_file}')


if __name__ == '__main__':
    create_backup()
    cleanup_backups()
