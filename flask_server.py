#!/usr/bin/env python3

import os
import sqlite3

import bcrypt
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, current_user
from flask_limiter import Limiter

app = Flask(__name__)
app.secret_key = os.environ.get('BITCOIN_GITHUB_SK')
limiter = Limiter(key_func=lambda: request.remote_addr if request else None, app=app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id


# User loader
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# Helper function to get the user from the database
def get_user(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=?', (username, ))
    user = cursor.fetchone()
    conn.close()
    return user


# Helper function to validate the password
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def is_valid_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    return True

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        token = request.form.get('token')
        username = request.form.get('username')
        password = request.form.get('password')

        if not token or not username or not password or not is_valid_password(password):
            return abort(400)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_tokens WHERE token = ? AND used = 0', (token, ))
        token_entry = cursor.fetchone()

        if not token_entry:
            conn.close()
            print("missing token in db")
            return abort(400)

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            cursor.execute('UPDATE user_tokens SET used = 1 WHERE id = ?', (token_entry[0], ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            print("IntegrityError")
            return abort(400)

        conn.close()
        return redirect(url_for('login'))
    else:
        token = request.args.get('token')
        return render_template('register.html', token=token)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate the user from the database
        user = get_user(username)

        if user and check_password(user[2], password):
            login_user(User(user[0]))
            return redirect(url_for('index'))
        else:
            return abort(401)
    else:
        return render_template('login.html')


def closed_by_count(issues):
    count = 0
    for issue in issues:
        if issue[15] is not None:
            count += 1
    return count


app.jinja_env.filters['closed_by_count'] = closed_by_count


def connect_db(db_name='issues.db'):
    conn = sqlite3.connect(db_name)
    return conn


def get_issues(conn):
    cursor = conn.cursor()
    query = f'''SELECT * FROM issues WHERE state='open' '''
    cursor.execute(query)
    issues = cursor.fetchall()
    for i, issue in enumerate(issues):
        issues[i] = list(issue)
        issues[i][7] = issue[7].split(',')
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
    conn = connect_db()
    issues = get_issues(conn)
    conn.close()
    return render_template('index.html', issues=issues, order='asc')


@app.route('/issue/<int:issue_id>')
def issue(issue_id):
    conn = connect_db()
    issue = get_issue(conn, issue_id)
    conn.close()
    return render_template('issue.html', issue=issue)


@app.route('/save/<int:issue_id>', methods=['POST'])
def save(issue_id):
    if not current_user.is_authenticated:
        return jsonify({'status': 'unauthorized'}), 401
    conn = connect_db()
    notes = request.form.get('notes', '').strip()
    attention_of = request.form.get('attention_of', '').strip()
    kill_factor = request.form.get('kill_factor', None)
    update_issue(conn, issue_id, notes, attention_of, kill_factor)
    conn.close()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
