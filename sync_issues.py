#!/usr/bin/env python3

import requests
import sqlite3
import os
import json

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    print('Please set your GitHub personal access token in the GITHUB_TOKEN environment variable')
    exit(1)

API_URL = 'https://api.github.com/repos/bitcoin/bitcoin/issues?per_page=500'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
}


def create_sync_status_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sync_status
                      (id INTEGER PRIMARY KEY, last_sync TEXT)''')
    conn.commit()


def get_last_sync_time(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT last_sync FROM sync_status WHERE id = 1')
    result = cursor.fetchone()
    return result[0] if result else None


def update_last_sync_time(conn, last_sync_time):
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO sync_status (id, last_sync) VALUES (1, ?)', (last_sync_time, ))
    conn.commit()


from datetime import datetime


def fetch_issues(url, last_sync_time):
    issues = []
    page = 1

    if last_sync_time:
        last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%dT%H:%M:%SZ')

    for state in ['open', 'closed']:
        while True:
            if last_sync_time:
                response = requests.get(f'{url}&state={state}&page={page}&since={last_sync_time.isoformat()}Z', headers=HEADERS)
            else:
                response = requests.get(f'{url}&state={state}&page={page}', headers=HEADERS)

            response.raise_for_status()
            new_issues = response.json()

            if not new_issues:
                break

            # Filter out pull requests
            new_issues = [issue for issue in new_issues if 'pull_request' not in issue]

            issues.extend(new_issues)
            page += 1

        page = 1

    return issues


def connect_db(db_name='issues.db'):
    conn = sqlite3.connect(db_name)
    return conn


def create_issues_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues
                      (id INTEGER PRIMARY KEY, number INTEGER, title TEXT, user TEXT, state TEXT, body TEXT, url TEXT, labels TEXT, created_at TEXT, updated_at TEXT, closed_at TEXT, closed_by TEXT, notes TEXT, attention_of TEXT, kill_factor INTEGER)'''
                   )
    conn.commit()


def insert_issue(conn, issue):
    cursor = conn.cursor()
    labels = ','.join([label['name'] for label in issue['labels']])
    user = json.dumps(issue['user'])
    created_at = issue['created_at']
    updated_at = issue['updated_at']
    closed_at = issue.get('closed_at', None)
    closed_by = json.dumps(issue.get('closed_by', None)) if issue.get('closed_by', None) else None

    cursor.execute('SELECT id FROM issues WHERE id = ?', (issue['id'], ))
    existing_issue = cursor.fetchone()

    if existing_issue:
        cursor.execute(
            '''UPDATE issues SET number = ?, title = ?, user = ?, state = ?, body = ?, url = ?, labels = ?, created_at = ?, updated_at = ?, closed_at = ?, closed_by = ? WHERE id = ?''',
            (issue['number'], issue['title'], user, issue['state'], issue['body'], issue['html_url'], labels, created_at, updated_at, closed_at, closed_by,
             issue['id']))
    else:
        cursor.execute(
            '''INSERT INTO issues (id, number, title, user, state, body, url, labels, created_at, updated_at, closed_at, closed_by, notes, attention_of, kill_factor)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)''',
            (issue['id'], issue['number'], issue['title'], user, issue['state'], issue['body'], issue['html_url'], labels, created_at, updated_at, closed_at,
             closed_by))

    conn.commit()


def sync_issues_to_db(issues, conn):
    create_issues_table(conn)
    for issue in issues:
        insert_issue(conn, issue)


def main():
    conn = connect_db()
    create_sync_status_table(conn)

    last_sync_time = get_last_sync_time(conn)
    issues = fetch_issues(API_URL, last_sync_time)
    sync_issues_to_db(issues, conn)

    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    update_last_sync_time(conn, now)

    conn.close()


if __name__ == '__main__':
    main()
