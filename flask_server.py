#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


def connect_db(db_name='issues.db'):
    conn = sqlite3.connect(db_name)
    return conn


def get_issues(conn, label_filter=None):
    cursor = conn.cursor()
    if label_filter:
        query = '''SELECT * FROM issues WHERE labels LIKE ? ORDER BY number ASC'''
        cursor.execute(query, (f'%{label_filter}%', ))
    else:
        query = '''SELECT * FROM issues ORDER BY number ASC'''
        cursor.execute(query)
    issues = cursor.fetchall()
    for i, issue in enumerate(issues):
        issues[i] = list(issue)
        issues[i][5] = issue[5].split(',')
    return issues


def get_issue(conn, issue_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM issues WHERE id=?', (issue_id, ))
    return cursor.fetchone()


def update_issue(conn, issue_id, notes, attention_of, kill_factor):
    cursor = conn.cursor()
    cursor.execute('UPDATE issues SET notes=?, attention_of=?, kill_factor=? WHERE id=?', (notes, attention_of, kill_factor, issue_id))
    conn.commit()


@app.route('/')
def index():
    label_filter = request.args.get('label', '').strip()
    conn = connect_db()
    issues = get_issues(conn, label_filter)
    conn.close()
    return render_template('index.html', issues=issues, label_filter=label_filter)


@app.route('/issue/<int:issue_id>')
def issue(issue_id):
    conn = connect_db()
    issue = get_issue(conn, issue_id)
    conn.close()
    return render_template('issue.html', issue=issue)


@app.route('/save/<int:issue_id>', methods=['POST'])
def save(issue_id):
    conn = connect_db()
    notes = request.form.get('notes', '').strip()
    attention_of = request.form.get('attention_of', '').strip()
    kill_factor = request.form.get('kill_factor', None)
    update_issue(conn, issue_id, notes, attention_of, kill_factor)
    conn.close()
    return redirect(url_for('issue', issue_id=issue_id))


if __name__ == '__main__':
    app.run(debug=True)
