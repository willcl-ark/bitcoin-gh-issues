#!/usr/bin/env python3

import shutil
import time
import os

DB_NAME = 'issues.db'
BACKUP_DIR = 'db_backups'

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

timestamp = time.strftime('%Y%m%d_%H%M%S')
backup_filename = f'{DB_NAME}_backup_{timestamp}.db'
backup_path = os.path.join(BACKUP_DIR, backup_filename)

shutil.copy2(DB_NAME, backup_path)
print(f'Database backup created: {backup_path}')
