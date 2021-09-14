import sqlite3

from athens.config import PATH_DB, app
from flask import g, current_app

def db():
    if 'db' not in g:
        needs_init = not PATH_DB.is_file()
        g.db = sqlite3.connect(
            PATH_DB,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        if needs_init:
            init_db(g.db)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()


def init_db(conn):
    with current_app.open_resource('schema.sql') as f:
        conn.executescript(f.read().decode('utf8'))
    cursor = conn.cursor()
    for action in ['ok','delete','skip']:
        cursor.execute('INSERT INTO queue_action (name) VALUES (?)', (action,))
    conn.commit()
