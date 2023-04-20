#!/usr/bin/env python3

import argparse
import os
import sqlite3
import secrets

import bcrypt

DB_PATH = os.environ.get('BITCOIN_GITHUB_DB_PATH')
if not DB_PATH:
    print('Please set the DB path in the BITCOIN_GITHUB_DB_PATH environment variable')
    exit(1)

WEB_ADDR = os.environ.get('BITCOIN_GITHUB_WEB_ADDR')
if not WEB_ADDR:
    print('Please set the website address in the BITCOIN_GITHUB_WEB_ADDR environment variable')
    exit(1)

def init_tokens_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                used BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        conn.commit()
    print("Initialized tokens table in the database")


def generate_token():
    token = secrets.token_urlsafe(32)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_tokens (token, used) VALUES (?, 0)', (token, ))
        conn.commit()
    return f"{WEB_ADDR}/register?token={token}"


def init_users_table():
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
    print("Initialized users table in the database")


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
    parser = argparse.ArgumentParser(description="Manage users and tokens in the database.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('init-users', help="Initialize the users table.")
    subparsers.add_parser('init-tokens', help="Initialize the tokens table.")

    add_user_parser = subparsers.add_parser('add', help="Add a new user.")
    add_user_parser.add_argument('username', help="The username of the new user.")
    add_user_parser.add_argument('password', help="The password of the new user.")

    subparsers.add_parser('token', help="Get a new login link.")

    args = parser.parse_args()

    if args.command == 'init-users':
        init_users_table()
    elif args.command == 'init-tokens':
        init_tokens_table()
    elif args.command == 'add':
        add_user(args.username, args.password)
    elif args.command == 'token':
        print(generate_token())


if __name__ == '__main__':
    main()
