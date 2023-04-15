#!/usr/bin/env python3

import requests
import sqlite3
import os

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    print('Please set your GitHub personal access token in the GITHUB_TOKEN environment variable')
    exit(1)

API_URL = 'https://api.github.com/repos/bitcoin/bitcoin/issues?state=open&per_page=100'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
}


def fetch_issues(url, state):
    issues = []
    page = 1

    while True:
        response = requests.get(f'{url}&state={state}&page={page}', headers=HEADERS)
        response.raise_for_status()
        new_issues = response.json()

        if not new_issues:
            break

        # Filter out pull requests
        new_issues = [issue for issue in new_issues if 'pull_request' not in issue]

        issues.extend(new_issues)
        page += 1

    return issues


def connect_db(db_name='issues.db'):
    conn = sqlite3.connect(db_name)
    return conn


def create_issues_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues
                      (id INTEGER PRIMARY KEY, number INTEGER, title TEXT, body TEXT, url TEXT, labels TEXT, notes TEXT, attention_of TEXT, kill_factor INTEGER)'''
                   )
    conn.commit()


def insert_issue(conn, issue):
    cursor = conn.cursor()
    labels = ','.join([label['name'] for label in issue['labels']])
    cursor.execute(
        '''INSERT OR IGNORE INTO issues (id, number, title, body, url, labels, notes, attention_of, kill_factor)
                      VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL)''', (issue['id'], issue['number'], issue['title'], issue['body'], issue['html_url'], labels))
    conn.commit()


def remove_closed_issues(conn, closed_issues):
    cursor = conn.cursor()
    for issue in closed_issues:
        cursor.execute('DELETE FROM issues WHERE id=?', (issue['id'], ))
    conn.commit()


def sync_issues_to_db(issues, conn):
    create_issues_table(conn)
    for issue in issues:
        insert_issue(conn, issue)


def main():
    open_issues = fetch_issues(API_URL, 'open')
    # closed_issues = fetch_issues(API_URL, 'closed')
    conn = connect_db()
    sync_issues_to_db(open_issues, conn)
    # remove_closed_issues(conn, closed_issues)
    conn.close()


if __name__ == '__main__':
    main()
