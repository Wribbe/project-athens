import sqlite3
import json

from athens.config import PATH_DB, app, PASSWORDS, PATH_PASSWORDS, ACTIONS
from flask import g, current_app

def db():
    if 'db' not in g:
        needs_init = not PATH_DB.is_file()
        g.db = sqlite3.connect(
            PATH_DB,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        if needs_init:
            _init_db(g.db)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()


def _init_db(conn):

    with current_app.open_resource('schema.sql') as f:
        conn.executescript(f.read().decode('utf8'))

    cursor = conn.cursor()

    for action in ACTIONS:
        cursor.execute('INSERT INTO queue_action (name) VALUES (?)', (action,))

    for username in PASSWORDS.values():
        cursor.execute("INSERT INTO user (name) VALUES (?)", (username,))

    conn.commit()
    cursor.close()


def password_set(user, password):
    current = json.loads(PATH_PASSWORDS.read_text())
    current[user] = password
    PATH_PASSWORDS.write_text(json.dumps(current, indent=2))


def users():
    cursor = db().cursor()
    users = cursor.execute("SELECT * FROM user").fetchall()
    cursor.close()
    return users


def queue_items(user):
    session = db()
    cursor = session.cursor()
    queue_items = cursor.execute("""
        SELECT
            queue_action.name AS action
            ,image.filename AS filename
            ,queue_item.confirmed AS confirmed
        FROM queue_item
            JOIN user ON user.id == queue_item.id_user
            JOIN image ON image.id == queue_item.id_image
            JOIN queue_action ON queue_action.id == queue_item.id_action
        WHERE
            user.name == ?
            AND NOT queue_item.confirmed
        ORDER BY image.filename ASC
    """, (user,)).fetchall()
    cursor.close()
    return queue_items


def action_set(user, action, num):
    session = db()
    cursor = session.cursor()
    cursor.execute("""
        UPDATE queue_item SET id_action = (
            SELECT id FROM queue_action WHERE queue_action.name = ?
        )
        WHERE
            queue_item.id_user = (
                SELECT id FROM user WHERE user.name = ?
            )
        AND
            queue_item.id_image = (
                SELECT id FROM image WHERE image.filename = ?
            )
    """, (action, user, queue_items(user)[num]['filename']))
    session.commit()
    cursor.close()
