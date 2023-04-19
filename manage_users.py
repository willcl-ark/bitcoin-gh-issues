#!/usr/bin/env python3

import os
import sqlite3
import bcrypt
import argparse

DB_PATH = os.environ.get('BITCOIN_GITHUB_DB_PATH')


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()


def add_user(username, password):
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            print(f"User '{username}' added successfully.")
        except sqlite3.IntegrityError:
            print(f"User '{username}' already exists.")


def main():
    parser = argparse.ArgumentParser(description="Manage users in the SQLite database.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    init_parser = subparsers.add_parser('init', help="Initialize the users table.")

    add_user_parser = subparsers.add_parser('add', help="Add a new user.")
    add_user_parser.add_argument('username', help="The username of the new user.")
    add_user_parser.add_argument('password', help="The password of the new user.")

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
    elif args.command == 'add':
        add_user(args.username, args.password)


if __name__ == '__main__':
    main()
