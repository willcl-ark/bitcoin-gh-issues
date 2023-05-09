#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.environ.get('BITCOIN_GITHUB_DB_PATH')


if not DB_PATH:
    print('Please set the DB path in the BITCOIN_GITHUB_DB_PATH environment variable')
    exit(1)


def null_kill_factor(conn):
    cursor = conn.cursor()
    set_value = "NULL"
    update_sql = f"UPDATE issues SET kill_factor = {set_value}"
    cursor.execute(update_sql)
    conn.commit()


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


if __name__ == "__main__":
    conn = connect_db()
    null_kill_factor(conn)
    conn.close()
