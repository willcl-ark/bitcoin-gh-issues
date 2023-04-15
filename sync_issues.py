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


def fetch_issues(url):
    issues = []
    page = 1

    for state in ['open', 'closed']:
        while True:
            print(f"Processing {state} issues on page {page}")
            response = requests.get(f'{url}&state={state}&page={page}', headers=HEADERS)
            response.raise_for_status()
            new_issues = response.json()

            if not new_issues:
                break

            # Filter out pull requests
            new_issues = [issue for issue in new_issues if 'pull_request' not in issue]

            issues.extend(new_issues)
            page += 1

        page = 1  # Reset the page variable for the next state

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
    cursor.execute(
        '''INSERT OR IGNORE INTO issues (id, number, title, user, state, body, url, labels, created_at, updated_at, closed_at, closed_by, notes, attention_of, kill_factor)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)''',
        (issue['id'], issue['number'], issue['title'], user, issue['state'], issue['body'], issue['html_url'], labels, created_at, updated_at, closed_at,
         closed_by))
    conn.commit()


def sync_issues_to_db(issues, conn):
    create_issues_table(conn)
    for issue in issues:
        insert_issue(conn, issue)


def main():
    all_issues = fetch_issues(API_URL)
    conn = connect_db()
    sync_issues_to_db(all_issues, conn)
    conn.close()


if __name__ == '__main__':
    main()
